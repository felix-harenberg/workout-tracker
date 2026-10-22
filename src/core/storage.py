"""Minimal SQLite storage for the Phase 1 feasibility test."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    id: int
    text: str
    created_at: str


class EntryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def add(self, text: str) -> Entry:
        created_at = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO entry (text, created_at) VALUES (?, ?)", (text, created_at)
            )
            return Entry(id=cursor.lastrowid, text=text, created_at=created_at)

    def list_all(self) -> list[Entry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, text, created_at FROM entry ORDER BY id DESC"
            ).fetchall()
        return [Entry(*row) for row in rows]
