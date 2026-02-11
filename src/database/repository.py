import sqlite3
import os
from src.core.exceptions import DatabaseError
from src.core.logger import logger

class LinkRepository:
    """Handles database operations for SaveLinks."""

    def __init__(self, db_path=None):
        if db_path is None:
            # Default to a hidden folder in user's home directory
            home_dir = os.path.expanduser("~")
            app_dir = os.path.join(home_dir, ".savelinks")
            if not os.path.exists(app_dir):
                os.makedirs(app_dir)
            self.db_path = os.path.join(app_dir, "savelinks.db")
        else:
            self.db_path = db_path
        
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _get_connection(self):
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()

    def _init_db(self):
        """Initializes the database schema."""
        try:
            conn = self.connection
            cursor = conn.cursor()
            # User table to store salt and a verification hash (to check password correctness)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    salt BLOB NOT NULL,
                    verifier BLOB NOT NULL
                )
            """)
            # Links table stores encrypted data as a BLOB
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError("Failed to initialize database.") from e

    def add_user(self, username: str, salt: bytes, verifier: bytes) -> int:
        """Adds a new user to the database."""
        try:
            conn = self.connection
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, salt, verifier) VALUES (?, ?, ?)",
                (username, salt, verifier)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise DatabaseError("User already exists.")
        except sqlite3.Error as e:
            logger.error(f"Failed to add user: {e}")
            raise DatabaseError("Failed to add user.") from e

    def get_user_credentials(self, username: str):
        """Retrieves user's salt and verifier."""
        try:
            conn = self.connection
            cursor = conn.cursor()
            cursor.execute("SELECT id, salt, verifier FROM users WHERE username = ?", (username,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Failed to get user credentials: {e}")
            raise DatabaseError("Failed to retrieve user.") from e

    def add_link(self, user_id: int, encrypted_data: bytes):
        """Adds an encrypted link blob."""
        try:
            conn = self.connection
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO links (user_id, encrypted_data) VALUES (?, ?)",
                (user_id, encrypted_data)
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to add link: {e}")
            raise DatabaseError("Failed to add link.") from e

    def get_links(self, user_id: int):
        """Retrieves all encrypted links for a user."""
        try:
            conn = self.connection
            cursor = conn.cursor()
            cursor.execute("SELECT id, encrypted_data FROM links WHERE user_id = ?", (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Failed to get links: {e}")
            raise DatabaseError("Failed to retrieve links.") from e

    def delete_link(self, link_id: int, user_id: int):
        """Deletes a link by ID."""
        try:
            conn = self.connection
            cursor = conn.cursor()
            cursor.execute("DELETE FROM links WHERE id = ? AND user_id = ?", (link_id, user_id))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to delete link: {e}")
            raise DatabaseError("Failed to delete link.") from e
