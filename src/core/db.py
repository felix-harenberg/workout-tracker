"""SQLite connection and schema migrations."""

import sqlite3
from pathlib import Path

# Each entry upgrades the schema by one version. Never edit a released migration;
# append a new one instead, so databases on existing phones can be upgraded.
MIGRATIONS: list[str] = [
    """
    CREATE TABLE exercise (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE
    );

    CREATE TABLE workout (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE workout_set (
        id INTEGER PRIMARY KEY,
        workout_id INTEGER NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        set_number INTEGER NOT NULL,
        reps INTEGER NOT NULL CHECK (reps > 0),
        weight_kg REAL CHECK (weight_kg IS NULL OR weight_kg >= 0)
    );

    CREATE INDEX idx_workout_set_workout ON workout_set(workout_id);
    """,
]

SCHEMA_VERSION = len(MIGRATIONS)


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the database, creating or upgrading the schema as needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for target, script in enumerate(MIGRATIONS[version:], start=version + 1):
        # executescript commits first; the explicit transaction keeps each step atomic.
        conn.executescript(f"BEGIN;\n{script}\nPRAGMA user_version = {target};\nCOMMIT;")
