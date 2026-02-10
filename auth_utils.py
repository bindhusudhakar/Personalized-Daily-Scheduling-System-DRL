import sqlite3
import bcrypt
from datetime import datetime
import jwt
import os
from typing import Optional, Tuple

DB_NAME = "poi_cache.db"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"


def init_users_table():
    """Create users table if it doesn't exist"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Users table ready!")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_user(email: str, password: str, full_name: str) -> Tuple[bool, str, Optional[int]]:
    """
    Create a new user account.
    Returns (success, message, user_id)
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already registered", None

        # Hash password and insert user
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name)
            VALUES (?, ?, ?)
        """, (email, password_hash, full_name))

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        return True, "User created successfully", user_id

    except Exception as e:
        return False, f"Error creating user: {str(e)}", None


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Authenticate user with email and password.
    Returns (success, message, user_data)
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, password_hash, full_name, created_at
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()
        conn.close()

        if not user:
            return False, "Invalid email or password", None

        user_id, user_email, password_hash, full_name, created_at = user

        if not verify_password(password, password_hash):
            return False, "Invalid email or password", None

        user_data = {
            "id": user_id,
            "email": user_email,
            "full_name": full_name,
            "created_at": created_at
        }

        return True, "Login successful", user_data

    except Exception as e:
        return False, f"Error during login: {str(e)}", None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Fetch user data by ID"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, full_name, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()
        conn.close()

        if not user:
            return None

        return {
            "id": user[0],
            "email": user[1],
            "full_name": user[2],
            "created_at": user[3]
        }

    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None


def get_all_users() -> list:
    """Fetch all users from the database"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, full_name, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users = cursor.fetchall()
        conn.close()

        return [
            {
                "id": user[0],
                "email": user[1],
                "full_name": user[2],
                "created_at": user[3]
            }
            for user in users
        ]

    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return []


def create_access_token(user_id: int) -> str:
    """Create JWT token for user"""
    try:
        payload = {
            "sub": str(user_id),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        print(f"✅ Token created successfully: {token[:20]}...")
        return token
    except Exception as e:
        print(f"❌ Error creating token: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verify_token(token: str) -> Optional[int]:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return None


def delete_user_by_id(user_id: int) -> Tuple[bool, str]:
    """Delete a user by ID"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        if cursor.rowcount == 0:
            conn.close()
            return False, "User not found"

        conn.commit()
        conn.close()
        return True, f"User {user_id} deleted successfully"

    except Exception as e:
        return False, f"Error deleting user: {str(e)}"


def delete_user_by_email(email: str) -> Tuple[bool, str]:
    """Delete a user by email"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE email = ?", (email,))

        if cursor.rowcount == 0:
            conn.close()
            return False, "User not found"

        conn.commit()
        conn.close()
        return True, f"User {email} deleted successfully"

    except Exception as e:
        return False, f"Error deleting user: {str(e)}"


def delete_all_users() -> Tuple[bool, str]:
    """Delete all users from the table (use with caution!)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users")
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()
        return True, f"Deleted {deleted_count} users from the database"

    except Exception as e:
        return False, f"Error deleting users: {str(e)}"
