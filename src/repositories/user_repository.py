import sqlite3
from models.user import User

class UserRepository:

    def __init__(self, db_path="data/app.db"):
        self.db_path = db_path

    def get_by_email(self, email: str) -> User | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, username, password_hash, is_active FROM users WHERE email=?",
            (email,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return User(*row)

    def create(self, user: User):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (id, email, username, password_hash, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.email,
            user.username,
            user.password_hash,
            user.is_active
        ))

        conn.commit()
        conn.close()
