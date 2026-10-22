"""CSV export of all data: one row per set, ready for pandas."""

import csv
import io
import sqlite3
from datetime import date

from core.training import format_weight

CSV_COLUMNS = [
    "workout_id",
    "date",
    "workout_name",
    "workout_notes",
    "exercise",
    "set_number",
    "reps",
    "weight_kg",
]


def export_csv(conn: sqlite3.Connection) -> str:
    """All workouts and sets, oldest first. Workouts without sets get one row with
    empty set columns; an empty weight_kg means a bodyweight set."""
    rows = conn.execute(
        """
        SELECT w.id, w.date, w.name, w.notes, e.name, s.set_number, s.reps, s.weight_kg
        FROM workout w
        LEFT JOIN workout_set s ON s.workout_id = w.id
        LEFT JOIN exercise e ON e.id = s.exercise_id
        ORDER BY w.date, w.id, s.id
        """
    ).fetchall()

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for *values, weight_kg in rows:
        writer.writerow([*values, format_weight(weight_kg) if weight_kg is not None else ""])
    return buffer.getvalue()


def export_filename(today: date) -> str:
    return f"workout-tracker-{today.isoformat()}.csv"
