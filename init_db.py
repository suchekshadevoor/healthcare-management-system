import sqlite3
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

cur.execute('PRAGMA table_info(users)')
columns = [row[1] for row in cur.fetchall()]
if 'is_admin' not in columns:
    cur.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0')

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
