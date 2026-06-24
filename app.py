import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import DB_NAME, get_connection, init_database


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "beginner-dev-secret-change-later")


def query_db(sql, params=(), one=False):
    """Read rows from SQLite and return sqlite3.Row objects."""
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows[0] if one and rows else (None if one else rows)


def execute_db(sql, params=()):
    """Run INSERT/UPDATE/DELETE queries."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return query_db("SELECT id, name, email FROM users WHERE id = ?", (user_id,), one=True)


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Please login to continue.", "error")
            return redirect(url_for("login"))
        return route_function(*args, **kwargs)

    return wrapper


@app.context_processor
def inject_common_data():
    return {"current_user": current_user(), "year": datetime.now().year}


@app.route("/")
def home():
    # The first page of the application should be the login page.
    if current_user():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("login"))

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid login. Please check your email and password.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))
        if query_db("SELECT id FROM users WHERE email = ?", (email,), one=True):
            flash("This email is already registered.", "error")
            return redirect(url_for("register"))

        execute_db(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "hospitals": query_db("SELECT COUNT(*) AS total FROM hospitals", one=True)["total"],
        "doctors": query_db("SELECT COUNT(*) AS total FROM doctors", one=True)["total"],
        "appointments": query_db(
            "SELECT COUNT(*) AS total FROM appointments WHERE user_id = ?",
            (current_user()["id"],),
            one=True,
        )["total"],
        "beds": query_db("SELECT COALESCE(SUM(beds_available), 0) AS total FROM hospitals", one=True)["total"],
    }
    latest_hospitals = query_db("SELECT * FROM hospitals ORDER BY name LIMIT 4")
    return render_template("dashboard.html", stats=stats, hospitals=latest_hospitals)


@app.route("/hospitals")
@login_required
def hospitals():
    hospital_type = request.args.get("type", "")
    if hospital_type in {"Government", "Private"}:
        rows = query_db("SELECT * FROM hospitals WHERE type = ? ORDER BY name", (hospital_type,))
    else:
        rows = query_db("SELECT * FROM hospitals ORDER BY name")
    return render_template("hospitals.html", hospitals=rows, selected_type=hospital_type)


@app.route("/doctors")
@login_required
def doctors():
    rows = query_db(
        """
        SELECT doctors.*, hospitals.name AS hospital_name
        FROM doctors
        JOIN hospitals ON hospitals.id = doctors.hospital_id
        ORDER BY doctors.name
        """
    )
    return render_template("doctors.html", doctors=rows)


@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    if request.method == "POST":
        hospital_id = request.form.get("hospital_id")
        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")

        if not hospital_id or not doctor_id or not appointment_date or not appointment_time:
            flash("Please select hospital, doctor, date, and time.", "error")
            return redirect(url_for("appointments"))

        try:
            execute_db(
                """
                INSERT INTO appointments (user_id, hospital_id, doctor_id, appointment_date, appointment_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (current_user()["id"], hospital_id, doctor_id, appointment_date, appointment_time),
            )
            flash("Appointment booked successfully.", "success")
            return redirect(url_for("appointments"))
        except sqlite3.IntegrityError:
            flash("This doctor is already booked at that date and time.", "error")

    hospitals_rows = query_db("SELECT id, name FROM hospitals ORDER BY name")
    doctors_rows = query_db(
        """
        SELECT doctors.*, hospitals.name AS hospital_name
        FROM doctors
        JOIN hospitals ON hospitals.id = doctors.hospital_id
        ORDER BY doctors.name
        """
    )
    appointment_rows = query_db(
        """
        SELECT appointments.*, hospitals.name AS hospital_name, doctors.name AS doctor_name
        FROM appointments
        JOIN hospitals ON hospitals.id = appointments.hospital_id
        JOIN doctors ON doctors.id = appointments.doctor_id
        WHERE appointments.user_id = ?
        ORDER BY appointments.appointment_date DESC, appointments.appointment_time DESC
        """,
        (current_user()["id"],),
    )
    return render_template(
        "appointments.html",
        hospitals=hospitals_rows,
        doctors=doctors_rows,
        appointments=appointment_rows,
    )


@app.route("/appointments/book/<int:doctor_id>")
@login_required
def book_from_doctor(doctor_id):
    doctor = query_db("SELECT hospital_id FROM doctors WHERE id = ?", (doctor_id,), one=True)
    if not doctor:
        flash("Doctor not found.", "error")
        return redirect(url_for("doctors"))
    return redirect(url_for("appointments", doctor_id=doctor_id, hospital_id=doctor["hospital_id"]))


@app.route("/map")
@login_required
def map_view():
    rows = query_db("SELECT * FROM hospitals WHERE latitude != 0 AND longitude != 0 ORDER BY name")
    return render_template("map.html", hospitals=rows)


@app.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html")


@app.route("/api/doctors/<int:hospital_id>")
@login_required
def api_doctors_by_hospital(hospital_id):
    rows = query_db(
        "SELECT id, name, specialization, availability FROM doctors WHERE hospital_id = ? ORDER BY name",
        (hospital_id,),
    )
    return jsonify([dict(row) for row in rows])


@app.route("/api/chatbot", methods=["POST"])
@login_required
def api_chatbot():
    message = (request.get_json() or {}).get("message", "").lower()
    if "hello" in message or "hi" in message:
        reply = "Hello! How can I help you?"
    elif "hospital" in message:
        reply = "Open the Hospitals page to view hospital type, beds, oxygen, and city."
    elif "appointment" in message or "doctor" in message:
        reply = "Use the Appointments page to select a hospital, doctor, date, and time."
    elif "oxygen" in message or "bed" in message:
        reply = "You can check bed and oxygen availability on the Hospitals page."
    else:
        reply = "I can help with hospitals, doctors, appointments, beds, and oxygen information."
    return jsonify({"reply": reply})


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


init_database()


if __name__ == "__main__":
    print(f"Using SQLite database: {DB_NAME}")
    app.run(debug=True, use_reloader=False)
