import json
import sqlite3
import uuid
from pathlib import Path


class SessionManager:

    def __init__(self, data_dir: str):
        Path(data_dir).mkdir(
            parents=True,
            exist_ok=True
        )

        self.db_path = str(
            Path(data_dir) / "sessions.db"
        )

        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    runtime_session_id TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)

    def create(self) -> str:
        session_id = str(uuid.uuid4())

        with self._connect() as db:
            db.execute(
                "INSERT INTO sessions (id) VALUES (?)",
                (session_id,)
            )

        return session_id

    def get(self, session_id: str):
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "runtime_session_id": row[1],
            "metadata": json.loads(row[2])
        }

    def update_runtime_session(
        self,
        session_id: str,
        runtime_session_id: str
    ):
        with self._connect() as db:
            db.execute(
                """
                UPDATE sessions
                SET runtime_session_id = ?
                WHERE id = ?
                """,
                (runtime_session_id, session_id)
            )
