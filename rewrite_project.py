from pathlib import Path

files = {
    "app.py": '''from pathlib import Path
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


def has_column(table, column):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(%s)" % table)
    columns = [row[1] for row in cursor.fetchall()]
    connection.close()
    return column in columns


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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """
    )

    if not has_column("users", "is_admin"):
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            beds INTEGER NOT NULL DEFAULT 0,
            doctors INTEGER NOT NULL DEFAULT 0,
            emergency INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@healthcare.com",))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
            (
                "Admin User",
                "admin@healthcare.com",
                generate_password_hash("Admin@123"),
                1,
            ),
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
''',
    "init_db.py": '''import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DATABASE = Path(__file__).resolve().parent / "database.db"
connection = sqlite3.connect(DATABASE)
cur = connection.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    beds INTEGER NOT NULL DEFAULT 0,
    doctors INTEGER NOT NULL DEFAULT 0,
    emergency INTEGER NOT NULL DEFAULT 0
)
''')

cur.execute('SELECT id FROM users WHERE email = ?', ('admin@healthcare.com',))
if cur.fetchone() is None:
    cur.execute(
        'INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)',
        ('Admin User', 'admin@healthcare.com', generate_password_hash('Admin@123'), 1),
    )

cur.execute('SELECT id FROM hospitals LIMIT 1')
if cur.fetchone() is None:
    hospitals = [
        ('City Horizon Hospital', 'Central City', 12, 4, 1),
        ('Greenleaf Medical', 'East Market', 8, 5, 1),
        ('Riverfront Care Center', 'River District', 5, 3, 0),
        ('Lakeside Health', 'North Valley', 7, 6, 1),
        ('Sunrise Emergency', 'South Gate', 2, 2, 1),
    ]
    cur.executemany(
        'INSERT INTO hospitals (name, location, beds, doctors, emergency) VALUES (?, ?, ?, ?, ?)',
        hospitals,
    )

connection.commit()
connection.close()
print('Database schema initialized successfully.')
''',
    "requirements.txt": "flask\ngunicorn\n",
    "templates/base.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Healthcare Availability System</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header class="site-header">
        <div class="brand">
            <a href="{{ url_for('home') }}">Healthcare Availability</a>
        </div>
        <nav class="site-nav">
            <a href="{{ url_for('home') }}">Home</a>
            {% if current_user %}
                <a href="{{ url_for('dashboard') }}">Dashboard</a>
                {% if current_user.is_admin %}
                    <a href="{{ url_for('add_hospital') }}">Add Hospital</a>
                {% endif %}
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('signup') }}">Sign Up</a>
            {% endif %}
        </nav>
    </header>

    <section class="flash-messages">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </section>

    <main class="content">
        {% block content %}{% endblock %}
    </main>

    <footer class="footer">
        <p>Built for responsive healthcare availability management.</p>
    </footer>

    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
''',
    "templates/index.html": '''{% extends "base.html" %}
{% block content %}
<section class="hero">
    <div class="hero-card">
        <div>
            <span class="eyebrow">Healthcare Availability System</span>
            <h1>Find hospitals with open beds, doctors, and emergency services in seconds.</h1>
            <p>Search, filter, and manage nearby healthcare availability with real-time dashboard tools.</p>
            <div class="hero-actions">
                <a class="button button-primary" href="{{ url_for('dashboard') }}">View Hospitals</a>
                <a class="button button-secondary" href="{{ url_for('signup') }}">Create Account</a>
            </div>
        </div>
        <div class="hero-panel">
            <div class="metric-card">
                <span>150+</span>
                <p>Hospital locations</p>
            </div>
            <div class="metric-card">
                <span>24/7</span>
                <p>Emergency monitoring</p>
            </div>
        </div>
    </div>
</section>
<section class="feature-grid">
    <article class="feature-card">
        <h3>Live availability</h3>
        <p>Filter hospitals by beds, doctors, and emergency readiness instantly.</p>
    </article>
    <article class="feature-card">
        <h3>Admin controls</h3>
        <p>Authorized staff can update availability and add new hospitals.</p>
    </article>
    <article class="feature-card">
        <h3>Secure login</h3>
        <p>User accounts with password hashing and session-based access.</p>
    </article>
</section>
{% endblock %}
''',
    "templates/login.html": '''{% extends "base.html" %}
{% block content %}
<section class="auth-page">
    <div class="auth-card">
        <h2>Login to your account</h2>
        <form method="POST" class="auth-form">
            <label>Email</label>
            <input type="email" name="email" placeholder="Email" required>
            <label>Password</label>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="button button-primary">Login</button>
        </form>
        <p class="small-note">New user? <a href="{{ url_for('signup') }}">Create an account</a></p>
    </div>
</section>
{% endblock %}
''',
    "templates/register.html": '''{% extends "base.html" %}
{% block content %}
<section class="auth-page">
    <div class="auth-card">
        <h2>Create your account</h2>
        <form method="POST" class="auth-form">
            <label>Full name</label>
            <input type="text" name="name" placeholder="Your name" required>
            <label>Email</label>
            <input type="email" name="email" placeholder="Email" required>
            <label>Password</label>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="button button-primary">Register</button>
        </form>
        <p class="small-note">Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
    </div>
</section>
{% endblock %}
''',
    "templates/dashboard.html": '''{% extends "base.html" %}
{% block content %}
<section class="dashboard-page" data-page="dashboard" data-admin="{{ 'true' if is_admin else 'false' }}">
    <div class="dashboard-panel">
        <div class="dashboard-header">
            <div>
                <p class="eyebrow">Hospital Dashboard</p>
                <h1>Manage availability across all locations</h1>
            </div>
            <div class="dashboard-actions">
                <input id="searchHospital" type="search" placeholder="Search hospitals or city">
                <button id="resetFilters" class="button button-secondary">Reset filters</button>
            </div>
        </div>
        <div class="filters-row">
            <label><input type="checkbox" id="bedsOnly"> Has beds</label>
            <label><input type="checkbox" id="doctorsOnly"> Has doctors</label>
            <label><input type="checkbox" id="emergencyOnly"> Emergency available</label>
        </div>
        <div class="stats-row">
            <div class="stat-card"><span id="statHospitals">0</span><p>Hospitals</p></div>
            <div class="stat-card"><span id="statBeds">0</span><p>Beds available</p></div>
            <div class="stat-card"><span id="statDoctors">0</span><p>Doctors available</p></div>
            <div class="stat-card"><span id="statEmergency">0</span><p>Emergency units</p></div>
        </div>
        <div id="loadingState" class="loading-panel hidden">Loading hospital data…</div>
        <div id="dashboardEmpty" class="empty-state hidden">No hospitals match your filters.</div>
        <div id="hospitalGrid" class="hospital-grid"></div>
    </div>
</section>
{% endblock %}
''',
    "templates/add_hospital.html": '''{% extends "base.html" %}
{% block content %}
<section class="admin-page">
  <div class="admin-card">
    <h2>Add New Hospital</h2>
    <p>Create a new hospital entry with beds, doctors, and emergency status.</p>
    <form method="POST" class="admin-form">
      <label>Hospital name</label>
      <input type="text" name="name" placeholder="Hospital name" required>
      <label>Location</label>
      <input type="text" name="location" placeholder="City or district" required>
      <label>Beds available</label>
      <input type="number" name="beds" placeholder="0" min="0" value="0" required>
      <label>Doctors available</label>
      <input type="number" name="doctors" placeholder="0" min="0" value="0" required>
      <label>Emergency units</label>
      <input type="number" name="emergency" placeholder="0" min="0" value="0" required>
      <button type="submit" class="button button-primary">Add Hospital</button>
    </form>
  </div>
</section>
{% endblock %}
''',
    "static/js/app.js": '''const pageType = document.body.dataset.page;
const isAdmin = document.body.dataset.admin === 'true';

window.addEventListener('DOMContentLoaded', () => {
  if (pageType === 'dashboard') {
    initDashboard();
  }
});

function initDashboard() {
  const searchInput = document.getElementById('searchHospital');
  const bedsOnly = document.getElementById('bedsOnly');
  const doctorsOnly = document.getElementById('doctorsOnly');
  const emergencyOnly = document.getElementById('emergencyOnly');
  const resetFilters = document.getElementById('resetFilters');
  const hospitalGrid = document.getElementById('hospitalGrid');
  const loadingState = document.getElementById('loadingState');
  const emptyState = document.getElementById('dashboardEmpty');
  const statHospitals = document.getElementById('statHospitals');
  const statBeds = document.getElementById('statBeds');
  const statDoctors = document.getElementById('statDoctors');
  const statEmergency = document.getElementById('statEmergency');

  const refreshList = debounce(async () => {
    showLoading(true);
    const hospitals = await fetchHospitals();
    renderHospitalList(hospitals);
    showLoading(false);
  }, 250);

  searchInput?.addEventListener('input', refreshList);
  bedsOnly?.addEventListener('change', refreshList);
  doctorsOnly?.addEventListener('change', refreshList);
  emergencyOnly?.addEventListener('change', refreshList);
  resetFilters?.addEventListener('click', () => {
    if (searchInput) searchInput.value = '';
    if (bedsOnly) bedsOnly.checked = false;
    if (doctorsOnly) doctorsOnly.checked = false;
    if (emergencyOnly) emergencyOnly.checked = false;
    refreshList();
  });

  hospitalGrid?.addEventListener('click', async (event) => {
    const target = event.target;
    if (!target.classList.contains('button-update')) {
      return;
    }

    const card = target.closest('.hospital-card');
    if (!card) {
      return;
    }

    const id = card.dataset.id;
    const beds = Number(card.querySelector('[name="beds"]').value);
    const doctors = Number(card.querySelector('[name="doctors"]').value);
    const emergency = Number(card.querySelector('[name="emergency"]').value);

    await updateAvailability({ id, beds, doctors, emergency });
    refreshList();
  });

  refreshList();
  setInterval(refreshList, 15000);
}

async function fetchHospitals() {
  const searchValue = document.getElementById('searchHospital')?.value || '';
  const bedsOnly = document.getElementById('bedsOnly')?.checked;
  const doctorsOnly = document.getElementById('doctorsOnly')?.checked;
  const emergencyOnly = document.getElementById('emergencyOnly')?.checked;

  const params = new URLSearchParams();
  if (searchValue) params.set('search', searchValue);
  if (bedsOnly) params.set('beds', 'true');
  if (doctorsOnly) params.set('doctors', 'true');
  if (emergencyOnly) params.set('emergency', 'true');

  const response = await fetch(`/api/hospitals?${params.toString()}`);
  if (!response.ok) {
    console.error('Failed to load hospital data');
    return [];
  }

  return response.json();
}

function renderHospitalList(hospitals) {
  const hospitalGrid = document.getElementById('hospitalGrid');
  const emptyState = document.getElementById('dashboardEmpty');
  const statHospitals = document.getElementById('statHospitals');
  const statBeds = document.getElementById('statBeds');
  const statDoctors = document.getElementById('statDoctors');
  const statEmergency = document.getElementById('statEmergency');

  if (!hospitalGrid || !statHospitals || !statBeds || !statDoctors || !statEmergency || !emptyState) {
    return;
  }

  if (hospitals.length === 0) {
    hospitalGrid.innerHTML = '';
    emptyState.classList.remove('hidden');
    statHospitals.textContent = '0';
    statBeds.textContent = '0';
    statDoctors.textContent = '0';
    statEmergency.textContent = '0';
    return;
  }

  emptyState.classList.add('hidden');
  hospitalGrid.innerHTML = hospitals.map(renderHospitalCard).join('');

  const totals = hospitals.reduce(
    (acc, hospital) => {
      acc.beds += Number(hospital.beds);
      acc.doctors += Number(hospital.doctors);
      acc.emergency += Number(hospital.emergency);
      return acc;
    },
    { beds: 0, doctors: 0, emergency: 0 }
  );

  statHospitals.textContent = String(hospitals.length);
  statBeds.textContent = String(totals.beds);
  statDoctors.textContent = String(totals.doctors);
  statEmergency.textContent = String(totals.emergency);
}

function renderHospitalCard(hospital) {
  const bedStatus = hospital.beds > 0 ? 'Available' : 'Full';
  const doctorStatus = hospital.doctors > 0 ? 'Available' : 'Busy';
  const emergencyStatus = hospital.emergency > 0 ? 'Online' : 'Offline';
  const adminSection = isAdmin
    ? `
        <div class="admin-controls">
          <label>
            Beds available
            <input name="beds" type="number" min="0" value="${hospital.beds}" />
          </label>
          <label>
            Doctors available
            <input name="doctors" type="number" min="0" value="${hospital.doctors}" />
          </label>
          <label>
            Emergency units
            <input name="emergency" type="number" min="0" value="${hospital.emergency}" />
          </label>
          <button type="button" class="button button-primary button-update">Save update</button>
        </div>
      `
    : '';

  return `
    <article class="hospital-card" data-id="${hospital.id}">
      <div class="hospital-card-header">
        <div>
          <h3>${hospital.name}</h3>
          <p>${hospital.location}</p>
        </div>
        <span class="badge ${hospital.emergency > 0 ? 'status-ok' : 'status-low'}">${emergencyStatus}</span>
      </div>
      <div class="hospital-stats">
        <div><strong>${hospital.beds}</strong><span>Beds</span></div>
        <div><strong>${hospital.doctors}</strong><span>Doctors</span></div>
        <div><strong>${hospital.emergency}</strong><span>Emergency</span></div>
      </div>
      ${adminSection}
    </article>
  `;
}

function showLoading(show) {
  const loadingState = document.getElementById('loadingState');
  loadingState?.classList.toggle('hidden', !show);
}

async function updateAvailability(payload) {
  const response = await fetch('/update-availability', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const result = await response.json();
  if (!response.ok) {
    toast(result.message || 'Unable to update availability.');
    return;
  }

  toast(result.message || 'Availability updated.');
}

function toast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast-message';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3200);
}

function debounce(callback, delay = 180) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => callback(...args), delay);
  };
}
''',
    "static/css/style.css": '''@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  color-scheme: dark;
  font-family: 'Inter', system-ui, sans-serif;
  background-color: #050b1d;
  color: #e2e8f0;
  --surface: rgba(255,255,255,0.08);
  --surface-strong: rgba(255,255,255,0.14);
  --border: rgba(255,255,255,0.12);
  --primary: #38bdf8;
  --primary-strong: #0ea5e9;
  --success: #22c55e;
  --danger: #f97316;
  --muted: #94a3b8;
}

* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
  background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.14), transparent 28%),
    radial-gradient(circle at bottom right, rgba(124, 58, 237, 0.12), transparent 24%),
    #050b1d;
  color: #e2e8f0;
}

body {
  font-size: 16px;
  line-height: 1.6;
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input,
textarea,
select {
  font: inherit;
}

button {
  cursor: pointer;
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  background: rgba(4, 12, 33, 0.88);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 20;
}

.brand a {
  color: #ffffff;
  font-weight: 700;
  font-size: 1.1rem;
}

.site-nav {
  display: flex;
  align-items: center;
  gap: 20px;
}

.site-nav a {
  color: #cbd5e1;
  transition: color 0.2s ease;
}

.site-nav a:hover {
  color: #ffffff;
}

.flash-messages {
  width: min(1200px, calc(100% - 48px));
  margin: 16px auto 0;
}

.flash {
  padding: 14px 18px;
  border-radius: 14px;
  margin-bottom: 12px;
  max-width: 1200px;
  background: var(--surface);
  border: 1px solid rgba(255,255,255,0.08);
}

.flash.success {
  border-color: rgba(34, 197, 94, 0.35);
}

.flash.error {
  border-color: rgba(249, 115, 22, 0.35);
}

.content {
  width: min(1200px, calc(100% - 48px));
  margin: 32px auto 48px;
}

.hero {
  display: grid;
  grid-template-columns: 1.25fr 0.95fr;
  gap: 24px;
  padding: 40px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 32px;
}

.hero-card {
  display: grid;
  gap: 28px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--primary);
  font-size: 0.8rem;
}

.hero-card h1 {
  margin: 0;
  font-size: clamp(2rem, 3vw, 3.5rem);
  line-height: 1.05;
}

.hero-card p {
  max-width: 620px;
  color: #cbd5e1;
}

.hero-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: none;
  border-radius: 14px;
  padding: 14px 22px;
  font-weight: 600;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.button:hover {
  transform: translateY(-1px);
}

.button-primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
}

.button-secondary {
  border: 1px solid rgba(255,255,255,0.12);
  color: #e2e8f0;
  background: rgba(255,255,255,0.04);
}

.metric-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 22px;
  padding: 24px;
  display: grid;
  gap: 10px;
}

.metric-card span {
  font-size: 2rem;
  font-weight: 700;
}

.metric-card p {
  margin: 0;
  color: #94a3b8;
}

.feature-grid {
  margin-top: 32px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.feature-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 28px;
}

.feature-card h3 {
  margin-top: 0;
}

.auth-page,
.admin-page,
.dashboard-page {
  display: grid;
  place-items: center;
  min-height: calc(100vh - 160px);
}

.auth-card,
.admin-card {
  width: min(520px, 100%);
  padding: 36px;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 28px;
}

.auth-card h2,
.admin-card h2 {
  margin-top: 0;
}

.auth-form,
.admin-form {
  display: grid;
  gap: 16px;
}

.auth-form label,
.admin-form label {
  color: #94a3b8;
  font-size: 0.9rem;
}

.auth-form input,
.admin-form input,
.dashboard-actions input {
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
  color: #e2e8f0;
}

.small-note {
  color: #94a3b8;
}

.dashboard-panel {
  width: 100%;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 18px;
  margin-bottom: 24px;
}

.dashboard-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filters-row,
.stats-row {
  display: grid;
  gap: 14px;
  margin-bottom: 20px;
}

.filters-row {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.stats-row {
  grid-template-columns: repeat(4, minmax(140px, 1fr));
}

.stat-card {
  padding: 20px;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 24px;
  text-align: center;
}

.stat-card span {
  display: block;
  font-size: 2rem;
  font-weight: 700;
}

.hospital-grid {
  display: grid;
  gap: 18px;
}

.hospital-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 24px;
  display: grid;
  gap: 18px;
}

.hospital-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.hospital-card h3 {
  margin: 0;
}

.hospital-card p {
  margin: 4px 0 0;
  color: #94a3b8;
}

.hospital-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.hospital-stats div {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  padding: 18px;
  border-radius: 18px;
  text-align: center;
}

.hospital-stats strong {
  display: block;
  font-size: 1.6rem;
}

.hospital-stats span {
  color: #94a3b8;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-ok {
  background: rgba(34, 197, 94, 0.16);
  color: #86efac;
}

.status-low {
  background: rgba(249, 115, 22, 0.14);
  color: #fdba74;
}

.admin-controls {
  display: grid;
  gap: 14px;
  padding: 18px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
}

.admin-controls label {
  display: grid;
  gap: 8px;
  color: #cbd5e1;
}

.admin-controls input {
  width: 100%;
}

.loading-panel,
.empty-state {
  padding: 24px;
  margin-bottom: 18px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 20px;
}

.hidden {
  display: none !important;
}

.toast-message {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid rgba(255,255,255,0.08);
  padding: 14px 18px;
  border-radius: 16px;
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.22);
  z-index: 100;
}

.footer {
  text-align: center;
  color: #94a3b8;
  padding: 18px 0 6px;
}

@media (max-width: 940px) {
  .hero,
  .feature-grid,
  .stats-row,
  .hospital-stats {
    grid-template-columns: 1fr;
  }

  .dashboard-header {
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .site-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .site-nav {
    flex-wrap: wrap;
  }
}
'''
}

root = Path(__file__).resolve().parent
for relative_path, content in files.items():
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')

print('rewrite completed')
