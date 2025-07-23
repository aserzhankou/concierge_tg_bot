import sqlite3
import json
import logging
from datetime import datetime
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ChallengeStorage:
    def __init__(self, db_path="challenges.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    message_id INTEGER PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    answer INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection context manager"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                yield conn
            finally:
                conn.close()

    def add_challenge(self, message_id: int, chat_id: int, user_id: int, answer: int, expires_in_seconds: int = 180):
        """Add a new challenge to storage"""
        created_at = datetime.now()
        expires_at = datetime.now().timestamp() + expires_in_seconds
        
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO challenges 
                    (message_id, chat_id, user_id, answer, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (message_id, chat_id, user_id, answer, created_at.isoformat(), expires_at)
                )
                conn.commit()
                logger.debug(f"Added challenge for message {message_id} to database")
            except sqlite3.IntegrityError:
                logger.warning(f"Challenge with message_id {message_id} already exists")

    def get_challenge(self, message_id: int):
        """Get challenge by message ID"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM challenges WHERE message_id = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'message_id': row[0],
                    'chat_id': row[1],
                    'user_id': row[2],
                    'answer': row[3],
                    'created_at': datetime.fromisoformat(row[4]),
                    'expires_at': row[5]
                }
            return None

    def remove_challenge(self, message_id: int):
        """Remove a challenge from storage"""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM challenges WHERE message_id = ?",
                (message_id,)
            )
            conn.commit()
            logger.debug(f"Removed challenge {message_id} from database")

    def cleanup_expired(self):
        """Remove all expired challenges"""
        current_time = datetime.now().timestamp()
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM challenges WHERE expires_at < ?",
                (current_time,)
            )
            conn.commit()

    def get_user_challenges(self, chat_id: int, user_id: int):
        """Get all active challenges for a user in a chat"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM challenges 
                WHERE chat_id = ? AND user_id = ? AND expires_at > ?
                """,
                (chat_id, user_id, datetime.now().timestamp())
            )
            return [
                {
                    'message_id': row[0],
                    'chat_id': row[1],
                    'user_id': row[2],
                    'answer': row[3],
                    'created_at': datetime.fromisoformat(row[4]),
                    'expires_at': row[5]
                }
                for row in cursor.fetchall()
            ] 