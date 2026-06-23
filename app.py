from pathlib import Path
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-me-to-a-random-secret"
DATABASE = Path(__file__).resolve().parent / "database.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def query_db(query, args=(), one=False):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(query, args)
    rows = cursor.fetchall()
    connection.commit()
    connection.close()
    return rows[0] if one and rows else (rows if not one else None)


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return query_db("SELECT id, name, email, is_admin FROM users WHERE id = ?", (user_id,), one=True)


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


def init_db():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')

    cursor.execute('PRAGMA table_info(users)')
    user_columns = [row[1] for row in cursor.fetchall()]
    if 'is_admin' not in user_columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            beds INTEGER NOT NULL DEFAULT 0,
            doctors INTEGER NOT NULL DEFAULT 0,
            emergency INTEGER NOT NULL DEFAULT 0
        )
    ''')

    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@healthcare.com",))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
            ("Admin User", "admin@healthcare.com", generate_password_hash("Admin@123"), 1),
        )

    cursor.execute("SELECT id FROM hospitals LIMIT 1")
    if cursor.fetchone() is None:
        sample_hospitals = [
            ("City Horizon Hospital", "Central City", 12, 4, 1),
            ("Greenleaf Medical", "East Market", 8, 5, 1),
            ("Riverfront Care Center", "River District", 5, 3, 0),
            ("Lakeside Health", "North Valley", 7, 6, 1),
            ("Sunrise Emergency", "South Gate", 2, 2, 1),
        ]
        cursor.executemany(
            "INSERT INTO hospitals (name, location, beds, doctors, emergency) VALUES (?, ?, ?, ?, ?)",
            sample_hospitals,
        )

    connection.commit()
    connection.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html", page_name="home")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please complete all fields.", "error")
            return redirect(url_for("signup"))

        if query_db("SELECT id FROM users WHERE email = ?", (email,), one=True):
            flash("This email is already registered.", "error")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)
        connection = get_db()
        connection.execute(
            "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, 0),
        )
        connection.commit()
        connection.close()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", page_name="signup")


@app.route("/register")
def register():
    return redirect(url_for("signup"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html", page_name="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for("login"))

    return render_template("dashboard.html", page_name="dashboard", is_admin=bool(user["is_admin"]))


@app.route("/add-hospital", methods=["GET", "POST"])
def add_hospital():
    user = get_current_user()
    if not user:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    if not user["is_admin"]:
        flash("Admin access is required to add hospitals.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        beds = request.form.get("beds", "0")
        doctors = request.form.get("doctors", "0")
        emergency = request.form.get("emergency", "0")

        if not name or not location:
            flash("Hospital name and location are required.", "error")
            return redirect(url_for("add_hospital"))

        connection = get_db()
        connection.execute(
            "INSERT INTO hospitals (name, location, beds, doctors, emergency) VALUES (?, ?, ?, ?, ?)",
            (name, location, int(beds), int(doctors), int(emergency)),
        )
        connection.commit()
        connection.close()

        flash("Hospital added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_hospital.html", page_name="add_hospital")


@app.route("/api/hospitals")
def get_hospitals():
    search = request.args.get("search", "").strip()
    bed_only = request.args.get("beds") == "true"
    doctor_only = request.args.get("doctors") == "true"
    emergency_only = request.args.get("emergency") == "true"

    query = "SELECT * FROM hospitals"
    conditions = []
    args = []

    if search:
        conditions.append("(name LIKE ? OR location LIKE ?)")
        args.extend([f"%{search}%", f"%{search}%"])

    if bed_only:
        conditions.append("beds > 0")

    if doctor_only:
        conditions.append("doctors > 0")

    if emergency_only:
        conditions.append("emergency > 0")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY name COLLATE NOCASE"
    hospitals = query_db(query, args)

    return jsonify([dict(hospital) for hospital in hospitals])


@app.route("/update-availability", methods=["POST"])
def update_availability():
    user = get_current_user()
    if not user or not user["is_admin"]:
        return jsonify({"status": "error", "message": "Admin access is required."}), 401

    data = request.get_json() or {}
    hospital_id = data.get("id")
    beds = data.get("beds")
    doctors = data.get("doctors")
    emergency = data.get("emergency")

    if not hospital_id:
        return jsonify({"status": "error", "message": "Missing hospital ID."}), 400

    hospital = query_db("SELECT id FROM hospitals WHERE id = ?", (hospital_id,), one=True)
    if not hospital:
        return jsonify({"status": "error", "message": "Hospital not found."}), 404

    connection = get_db()
    connection.execute(
        "UPDATE hospitals SET beds = ?, doctors = ?, emergency = ? WHERE id = ?",
        (int(beds), int(doctors), int(emergency), hospital_id),
    )
    connection.commit()
    connection.close()

    return jsonify({"status": "success", "message": "Availability updated successfully."})


if __name__ == "__main__":
    app.run(debug=True)
