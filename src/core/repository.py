"""Save and load exercises, workouts and sets."""

import sqlite3
from datetime import date

from core.models import Exercise, Workout, WorkoutSet

# --- Exercises ---


def get_or_create_exercise(conn: sqlite3.Connection, name: str) -> Exercise:
    """Return the exercise with this name (ignoring case), creating it if needed."""
    name = name.strip()
    if not name:
        raise ValueError("Exercise name must not be empty")

    # Compared in Python because SQLite's NOCASE only folds ASCII (not "Ü").
    key = name.casefold()
    for exercise in list_exercises(conn):
        if exercise.name.casefold() == key:
            return exercise

    with conn:
        cursor = conn.execute("INSERT INTO exercise (name) VALUES (?)", (name,))
    return Exercise(id=cursor.lastrowid, name=name)


def get_exercise(conn: sqlite3.Connection, exercise_id: int) -> Exercise | None:
    row = conn.execute("SELECT id, name FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    return Exercise(*row) if row else None


def list_exercises(conn: sqlite3.Connection) -> list[Exercise]:
    rows = conn.execute("SELECT id, name FROM exercise ORDER BY name COLLATE NOCASE").fetchall()
    return [Exercise(*row) for row in rows]


# --- Workouts ---


def create_workout(
    conn: sqlite3.Connection, name: str, workout_date: date, notes: str = ""
) -> Workout:
    with conn:
        cursor = conn.execute(
            "INSERT INTO workout (name, date, notes) VALUES (?, ?, ?)",
            (name, workout_date.isoformat(), notes),
        )
    return Workout(id=cursor.lastrowid, name=name, date=workout_date, notes=notes)


def get_workout(conn: sqlite3.Connection, workout_id: int) -> Workout | None:
    row = conn.execute(
        "SELECT id, name, date, notes FROM workout WHERE id = ?", (workout_id,)
    ).fetchone()
    return _workout_from_row(row) if row else None


def list_workouts(conn: sqlite3.Connection) -> list[Workout]:
    """All workouts, newest first."""
    rows = conn.execute(
        "SELECT id, name, date, notes FROM workout ORDER BY date DESC, id DESC"
    ).fetchall()
    return [_workout_from_row(row) for row in rows]


def update_workout(
    conn: sqlite3.Connection, workout_id: int, name: str, workout_date: date, notes: str
) -> Workout:
    with conn:
        cursor = conn.execute(
            "UPDATE workout SET name = ?, date = ?, notes = ? WHERE id = ?",
            (name, workout_date.isoformat(), notes, workout_id),
        )
    if cursor.rowcount == 0:
        raise LookupError(f"No workout with id {workout_id}")
    return Workout(id=workout_id, name=name, date=workout_date, notes=notes)


def delete_workout(conn: sqlite3.Connection, workout_id: int) -> None:
    """Delete a workout and its sets. Exercises are kept for other workouts."""
    with conn:
        conn.execute("DELETE FROM workout WHERE id = ?", (workout_id,))


def _workout_from_row(row: tuple) -> Workout:
    workout_id, name, iso_date, notes = row
    return Workout(id=workout_id, name=name, date=date.fromisoformat(iso_date), notes=notes)


# --- Sets ---


def add_set(
    conn: sqlite3.Connection,
    workout_id: int,
    exercise_id: int,
    reps: int,
    weight_kg: float | None = None,
) -> WorkoutSet:
    """Log a set. Leave weight_kg as None for bodyweight exercises.

    The set number counts up per exercise within the workout.
    """
    _validate_set(reps, weight_kg)

    with conn:
        (set_number,) = conn.execute(
            "SELECT COALESCE(MAX(set_number), 0) + 1 FROM workout_set"
            " WHERE workout_id = ? AND exercise_id = ?",
            (workout_id, exercise_id),
        ).fetchone()
        cursor = conn.execute(
            "INSERT INTO workout_set (workout_id, exercise_id, set_number, reps, weight_kg)"
            " VALUES (?, ?, ?, ?, ?)",
            (workout_id, exercise_id, set_number, reps, weight_kg),
        )
    return WorkoutSet(
        id=cursor.lastrowid,
        workout_id=workout_id,
        exercise_id=exercise_id,
        set_number=set_number,
        reps=reps,
        weight_kg=weight_kg,
    )


def update_set(
    conn: sqlite3.Connection, set_id: int, reps: int, weight_kg: float | None
) -> WorkoutSet:
    _validate_set(reps, weight_kg)
    with conn:
        cursor = conn.execute(
            "UPDATE workout_set SET reps = ?, weight_kg = ? WHERE id = ?",
            (reps, weight_kg, set_id),
        )
    if cursor.rowcount == 0:
        raise LookupError(f"No set with id {set_id}")
    return _get_set(conn, set_id)


def delete_set(conn: sqlite3.Connection, set_id: int) -> None:
    """Delete a set and close the gap in the numbering of that exercise's sets."""
    with conn:
        row = conn.execute(
            "SELECT workout_id, exercise_id, set_number FROM workout_set WHERE id = ?",
            (set_id,),
        ).fetchone()
        if row is None:
            return
        workout_id, exercise_id, set_number = row
        conn.execute("DELETE FROM workout_set WHERE id = ?", (set_id,))
        conn.execute(
            "UPDATE workout_set SET set_number = set_number - 1"
            " WHERE workout_id = ? AND exercise_id = ? AND set_number > ?",
            (workout_id, exercise_id, set_number),
        )


def _validate_set(reps: int, weight_kg: float | None) -> None:
    if reps <= 0:
        raise ValueError("Reps must be positive")
    if weight_kg is not None and weight_kg < 0:
        raise ValueError("Weight must not be negative")


def _get_set(conn: sqlite3.Connection, set_id: int) -> WorkoutSet:
    row = conn.execute(
        "SELECT id, workout_id, exercise_id, set_number, reps, weight_kg"
        " FROM workout_set WHERE id = ?",
        (set_id,),
    ).fetchone()
    return WorkoutSet(*row)


def list_sets(conn: sqlite3.Connection, workout_id: int) -> list[WorkoutSet]:
    """All sets of a workout, in the order they were logged."""
    rows = conn.execute(
        "SELECT id, workout_id, exercise_id, set_number, reps, weight_kg"
        " FROM workout_set WHERE workout_id = ? ORDER BY id",
        (workout_id,),
    ).fetchall()
    return [WorkoutSet(*row) for row in rows]


def last_sets_for_exercise(
    conn: sqlite3.Connection, exercise_id: int, before: Workout
) -> tuple[Workout, list[WorkoutSet]] | None:
    """The most recent workout before `before` that includes this exercise, with its sets.

    Workouts on the same date count as earlier if they were created earlier.
    """
    row = conn.execute(
        "SELECT id, name, date, notes FROM workout"
        " WHERE (date < :date OR (date = :date AND id < :id))"
        " AND id IN (SELECT workout_id FROM workout_set WHERE exercise_id = :exercise_id)"
        " ORDER BY date DESC, id DESC LIMIT 1",
        {"date": before.date.isoformat(), "id": before.id, "exercise_id": exercise_id},
    ).fetchone()
    if row is None:
        return None
    workout = _workout_from_row(row)
    sets = [s for s in list_sets(conn, workout.id) if s.exercise_id == exercise_id]
    return workout, sets
