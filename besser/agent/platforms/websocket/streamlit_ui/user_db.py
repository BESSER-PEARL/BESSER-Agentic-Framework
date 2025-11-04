import psycopg2
import os
import json

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
                # Create a user_profiles table that stores JSON as text and references users.username
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        username VARCHAR(255) PRIMARY KEY REFERENCES users(username) ON DELETE CASCADE,
                        information TEXT
                    )
                """)

    def add_user(self, username, password):
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            return True
        except psycopg2.errors.UniqueViolation:
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

    def set_profile(self, username, profile_dict: dict) -> bool:
        """Upsert the profile JSON for the given username.

        If the user row does not exist, create it with an empty password (prototyping shortcut)
        so the FK constraint is satisfied.
        Returns True on success, False on error.
        """
        try:
            # Ensure user exists (create with empty password if not)
            if not self.user_exists(username):
                with self.conn:
                    with self.conn.cursor() as cur:
                        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, ""))

            json_str = json.dumps(profile_dict)
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO user_profiles (username, information)
                        VALUES (%s, %s)
                        ON CONFLICT (username) DO UPDATE SET information = EXCLUDED.information
                        """,
                        (username, json_str),
                    )
            return True
        except Exception:
            return False

    def get_profile(self, username):
        """Return profile dict for username or None if not found."""
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("SELECT information FROM user_profiles WHERE username=%s", (username,))
                    row = cur.fetchone()
                    if not row:
                        return None
                    info_text = row[0]
                    try:
                        return json.loads(info_text)
                    except Exception:
                        return None
        except Exception:
            return None
