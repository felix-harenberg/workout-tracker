"""CSV export of all data: one row per set or run, ready for pandas."""

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
    "workout_type",
    "exercise",
    "set_number",
    "reps",
    "weight_kg",
    "distance_km",
    "duration_s",
]


def export_csv(conn: sqlite3.Connection) -> str:
    """All workouts, oldest first: one row per set for strength workouts, one row per run.

    Strength workouts without sets get one row with empty set columns; an empty
    weight_kg means a bodyweight set.
    """
    rows = conn.execute(
        """
        SELECT w.id, w.date, w.name, w.notes, w.type,
               e.name, s.set_number, s.reps, s.weight_kg,
               r.distance_km, r.duration_s
        FROM workout w
        LEFT JOIN workout_set s ON s.workout_id = w.id
        LEFT JOIN exercise e ON e.id = s.exercise_id
        LEFT JOIN run r ON r.workout_id = w.id
        ORDER BY w.date, w.id, s.id
        """
    ).fetchall()

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for *before_weight, weight_kg, distance_km, duration_s in rows:
        writer.writerow(
            [
                *before_weight,
                _number(weight_kg),
                _number(distance_km),
                duration_s if duration_s is not None else "",
            ]
        )
    return buffer.getvalue()


def _number(value: float | None) -> str:
    return format_weight(value) if value is not None else ""


def export_filename(today: date) -> str:
    return f"workout-tracker-{today.isoformat()}.csv"
