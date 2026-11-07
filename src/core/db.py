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
    # v0.2: runs
    """
    ALTER TABLE workout ADD COLUMN type TEXT NOT NULL DEFAULT 'strength'
        CHECK (type IN ('strength', 'run'));

    CREATE TABLE run (
        workout_id INTEGER PRIMARY KEY REFERENCES workout(id) ON DELETE CASCADE,
        distance_km REAL NOT NULL CHECK (distance_km > 0),
        duration_s INTEGER NOT NULL CHECK (duration_s > 0)
    );
    """,
    # v0.4: reminder per exercise to go up or down in weight next time
    """
    ALTER TABLE exercise ADD COLUMN hint TEXT CHECK (hint IN ('up', 'down'));
    ALTER TABLE exercise ADD COLUMN hint_workout_id INTEGER
        REFERENCES workout(id) ON DELETE SET NULL;
    """,
    # v0.5: bodyweight, one entry per day, and small settings like the goal weight
    """
    CREATE TABLE bodyweight (
        date TEXT PRIMARY KEY,
        weight_kg REAL NOT NULL CHECK (weight_kg > 0)
    );

    CREATE TABLE setting (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
    # v0.6: notes on how to do an exercise ("Sitz auf Stufe 4"), shown every time
    """
    ALTER TABLE exercise ADD COLUMN notes TEXT NOT NULL DEFAULT '';
    """,
    # v0.6: supersets, groups of exercises done in turns. They belong to the workout, so
    # an exercise can be in a superset one day and alone the next. group_no 0, 1, ... is
    # shown as A, B, ...; position 0, 1, ... as A1, A2, ...
    """
    CREATE TABLE workout_superset (
        workout_id INTEGER NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        group_no INTEGER NOT NULL CHECK (group_no >= 0),
        position INTEGER NOT NULL CHECK (position >= 0),
        PRIMARY KEY (workout_id, exercise_id)
    );
    """,
    # v0.6: a name and notes per superset; a row only exists while the group does
    """
    CREATE TABLE workout_superset_info (
        workout_id INTEGER NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
        group_no INTEGER NOT NULL,
        name TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        PRIMARY KEY (workout_id, group_no)
    );
    """,
    # v0.6: running volume, only the kilometres (pace stays with the watch and Strava),
    # and a goal per week, keyed by its Monday
    """
    CREATE TABLE run_entry (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        distance_km REAL NOT NULL CHECK (distance_km > 0)
    );
    CREATE INDEX idx_run_entry_date ON run_entry(date);

    CREATE TABLE run_goal (
        week_start TEXT PRIMARY KEY,
        km REAL NOT NULL CHECK (km > 0)
    );
    """,
]

SCHEMA_VERSION = len(MIGRATIONS)


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the database, creating or upgrading the schema as needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Flet runs event handlers on worker threads; the app only ever does one thing at a time.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for target, script in enumerate(MIGRATIONS[version:], start=version + 1):
        # executescript commits first; the explicit transaction keeps each step atomic.
        conn.executescript(f"BEGIN;\n{script}\nPRAGMA user_version = {target};\nCOMMIT;")
