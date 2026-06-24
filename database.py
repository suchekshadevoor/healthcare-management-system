import csv
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "healthcare.db"
CSV_FILES = [BASE_DIR / "hospitals.csv", BASE_DIR / "hospital_dataset.csv"]


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all required tables if they do not already exist."""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            beds_available INTEGER NOT NULL DEFAULT 0,
            oxygen_available TEXT NOT NULL DEFAULT 'No',
            latitude REAL NOT NULL DEFAULT 0,
            longitude REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience INTEGER NOT NULL DEFAULT 0,
            availability TEXT NOT NULL,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            hospital_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
            UNIQUE (doctor_id, appointment_date, appointment_time)
        );
        """
    )
    conn.commit()
    conn.close()


def find_csv_file():
    for file_path in CSV_FILES:
        if file_path.exists():
            return file_path
    return None


def to_float(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def extract_city(address):
    """Simple beginner-friendly city extraction from address text."""
    if not address:
        return "Vijayapura"
    parts = address.split()
    return parts[-1] if parts else "Vijayapura"


def import_hospitals_from_csv():
    """Read hospital data from hospitals.csv or hospital_dataset.csv into SQLite."""
    csv_file = find_csv_file()
    if not csv_file:
        return

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) AS total FROM hospitals").fetchone()["total"]
    if count > 0:
        conn.close()
        return

    base_latitude = 16.8302
    base_longitude = 75.7100

    with csv_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader):
            name = (row.get("name") or row.get("Name") or "").strip()
            if not name:
                continue

            hospital_type = (row.get("type") or row.get("Type") or "Private").strip().title()
            if hospital_type not in {"Government", "Private"}:
                hospital_type = "Private"

            address = (row.get("address") or row.get("location") or row.get("Address") or "").strip()
            city = (row.get("city") or row.get("City") or extract_city(address)).strip()
            beds = int(float(row.get("beds") or row.get("beds_available") or 0))
            oxygen = (row.get("oxygen") or row.get("oxygen_available") or "No").strip().title()
            latitude = to_float(row.get("latitude") or row.get("lat"), base_latitude + index * 0.01)
            longitude = to_float(row.get("longitude") or row.get("lng"), base_longitude + index * 0.01)

            conn.execute(
                """
                INSERT OR IGNORE INTO hospitals
                (name, type, city, address, beds_available, oxygen_available, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, hospital_type, city, address, beds, oxygen, latitude, longitude),
            )

    conn.commit()
    conn.close()


def seed_users_and_doctors():
    """Add demo user and doctors so the project works immediately."""
    conn = get_connection()

    if not conn.execute("SELECT id FROM users WHERE email = ?", ("demo@care.com",)).fetchone():
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("Demo User", "demo@care.com", generate_password_hash("Demo@123")),
        )

    doctor_count = conn.execute("SELECT COUNT(*) AS total FROM doctors").fetchone()["total"]
    hospitals = conn.execute("SELECT id, name FROM hospitals ORDER BY id LIMIT 8").fetchall()

    if doctor_count == 0 and hospitals:
        specializations = [
            ("Dr. Ananya Rao", "General Medicine", 8, "Mon-Fri, 10 AM - 4 PM"),
            ("Dr. Kiran Shetty", "Cardiology", 12, "Mon/Wed/Fri, 9 AM - 1 PM"),
            ("Dr. Meera Kulkarni", "Pediatrics", 6, "Tue-Sat, 11 AM - 5 PM"),
            ("Dr. Prakash Patil", "Orthopedics", 10, "Mon-Sat, 10 AM - 2 PM"),
            ("Dr. Sana Khan", "Pulmonology", 9, "Mon/Thu/Sat, 12 PM - 6 PM"),
        ]
        for index, hospital in enumerate(hospitals):
            doctor = specializations[index % len(specializations)]
            conn.execute(
                """
                INSERT INTO doctors (hospital_id, name, specialization, experience, availability)
                VALUES (?, ?, ?, ?, ?)
                """,
                (hospital["id"], doctor[0], doctor[1], doctor[2], doctor[3]),
            )

    conn.commit()
    conn.close()


def init_database():
    create_tables()
    import_hospitals_from_csv()
    seed_users_and_doctors()


if __name__ == "__main__":
    init_database()
    print(f"Database created successfully: {DB_NAME}")
