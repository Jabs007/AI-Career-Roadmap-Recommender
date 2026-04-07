import os
import streamlit as st # type: ignore
import psycopg2 # type: ignore
import bcrypt # type: ignore
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "kuccps_jobs"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error connecting to db: {e}")
        return None

def init_db():
    conn = get_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                )
            """)
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255);")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255);")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;")
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255),
                    search_query TEXT,
                    mean_grade VARCHAR(10),
                    top_recommendation VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        conn.close()

def create_user(username, password, email="", first_name="", last_name=""):
    conn = get_connection()
    if not conn: return False
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)", 
                (username, hashed, email, first_name, last_name)
            )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False # User already exists
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result:
                return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))
    except Exception as e:
        print(e)
    finally:
        conn.close()
    return False

def get_or_create_google_user(email, first_name, last_name):
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            # 1. Check if email already registered
            cur.execute("SELECT username FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            if result:
                return result[0]
            
            # 2. Derive base username from email
            base_username = email.split('@')[0]
            username = base_username
            
            # Ensure uniqueness
            cur.execute("SELECT count(*) FROM users WHERE username = %s", (username,))
            if cur.fetchone()[0] > 0:
                import time
                username = f"{base_username}_{int(time.time() * 1000)}"
                
            # 3. Create user with dummy hash
            cur.execute(
                "INSERT INTO users (username, password_hash, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)", 
                (username, "OAUTH_GOOGLE_AUTH", email, first_name, last_name)
            )
        conn.commit()
        return username
    except Exception as e:
        print(f"Error in google auth db: {e}")
    finally:
        conn.close()
    return None

def is_user_admin(username):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT is_admin FROM users WHERE username = %s AND is_admin = TRUE", (username,))
            return cur.fetchone() is not None
    except Exception as e:
        print(e)
    finally:
        conn.close()
    return False

def get_all_users():
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, email, first_name, last_name, is_admin FROM users ORDER BY id ASC")
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching users: {e}")
    finally:
        conn.close()
    return []

def set_user_admin_status(username, status: bool):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET is_admin = %s WHERE username = %s", (status, username))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def log_user_activity(username, search_query, mean_grade, top_recommendation):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO activity_logs (username, search_query, mean_grade, top_recommendation) VALUES (%s, %s, %s, %s)",
                (username, search_query, mean_grade, top_recommendation)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False
    finally:
        conn.close()

def get_activity_logs():
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, search_query, mean_grade, top_recommendation, timestamp FROM activity_logs ORDER BY timestamp DESC")
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching logs: {e}")
    finally:
        conn.close()
    return []
