import psycopg2
from psycopg2 import errors
import os

def get_db_config():
    return {
        "host": os.environ.get("STREAMLIT_DB_HOST", "localhost"),
        "port": int(os.environ.get("STREAMLIT_DB_PORT", 5432)),
        "database": os.environ.get("STREAMLIT_DB_NAME", "besser_users"),
        "user": os.environ.get("STREAMLIT_DB_USER", "besser_user"),
        "password": os.environ.get("STREAMLIT_DB_PASSWORD", "besser_pass"),
    }

class UserDB:
    def __init__(self):
        self.conn = psycopg2.connect(**get_db_config())
        self.create_table()

    def create_table(self):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        username VARCHAR(255) PRIMARY KEY,
                        password VARCHAR(255) NOT NULL
                    )
                """)

    def add_user(self, username, password):
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            return True
        except errors.UniqueViolation:
            return False  # Username already exists
        except Exception:
            return False

    def authenticate(self, username, password):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                return cur.fetchone() is not None

    def user_exists(self, username):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                return cur.fetchone() is not None
