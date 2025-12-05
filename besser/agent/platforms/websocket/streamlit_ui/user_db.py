import psycopg2
from psycopg2 import errors
import os
import bcrypt

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
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            # store as text (decoded) to avoid byte/encoding mismatches with VARCHAR columns
            hashed_text = hashed_password.decode('utf-8')
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                                (username, hashed_text))
            return True
        except errors.UniqueViolation:
            return False

    def authenticate(self, username, password):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT password FROM users WHERE username=%s", (username,))
                result = cur.fetchone()
                if result:
                    stored = result[0]
                    # ensure stored is bytes for bcrypt.checkpw
                    if isinstance(stored, str):
                        stored_bytes = stored.encode('utf-8')
                    else:
                        stored_bytes = stored
                    return bcrypt.checkpw(password.encode('utf-8'), stored_bytes)
                return False

    def user_exists(self, username):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                return cur.fetchone() is not None
