import sqlite3
import hashlib
import os
from typing import Optional

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data_Tier/users.db'))

def init_db():
    """Initializes the SQLite database and creates the users table if it doesn't exist."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hashes a password securely using PBKDF2 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against its stored hash."""
    try:
        salt_hex, key_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return new_key == key
    except Exception:
        return False

def register_user(username: str, password: str) -> bool:
    """Registers a new user in the database. Returns True if successful, False if username exists."""
    username = username.strip().lower()
    if not username or not password:
        return False
    pw_hash = hash_password(password)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, pw_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> bool:
    """Validates user credentials. Returns True if successful, False otherwise."""
    username = username.strip().lower()
    if not username or not password:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return verify_password(password, row[0])
    return False
