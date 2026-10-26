"""Progress stats: personal records, max weight per day and weekly volume."""

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from core.models import WorkoutSet
from core.training import format_weight

_SET_COLUMNS = "s.id, s.workout_id, s.exercise_id, s.set_number, s.reps, s.weight_kg"


@dataclass(frozen=True)
class ExercisePR:
    """The heaviest set ever logged for an exercise."""

    workout_set: WorkoutSet
    date: date


def _weighted_sets(conn: sqlite3.Connection, exercise_id: int) -> list[tuple[date, WorkoutSet]]:
    """All sets with a weight for one exercise, oldest first. Bodyweight sets are skipped."""
    rows = conn.execute(
        f"SELECT w.date, {_SET_COLUMNS} FROM workout_set s"
        " JOIN workout w ON w.id = s.workout_id"
        " WHERE s.exercise_id = ? AND s.weight_kg IS NOT NULL"
        " ORDER BY w.date, s.id",
        (exercise_id,),
    ).fetchall()
    return [(date.fromisoformat(iso_date), WorkoutSet(*rest)) for iso_date, *rest in rows]


def exercise_pr(conn: sqlite3.Connection, exercise_id: int) -> ExercisePR | None:
    """Heaviest set; ties go to more reps. None if the exercise has no weighted sets."""
    sets = _weighted_sets(conn, exercise_id)
    if not sets:
        return None
    day, heaviest = max(sets, key=lambda ds: (ds[1].weight_kg, ds[1].reps))
    return ExercisePR(workout_set=heaviest, date=day)


def max_weight_history(conn: sqlite3.Connection, exercise_id: int) -> list[tuple[date, float]]:
    """Heaviest weight per training day, oldest first."""
    heaviest_per_day: dict[date, float] = {}
    for day, workout_set in _weighted_sets(conn, exercise_id):
        heaviest_per_day[day] = max(workout_set.weight_kg, heaviest_per_day.get(day, 0))
    return sorted(heaviest_per_day.items())


def format_tonnage(kg: float) -> str:
    """Total lifted weight with Swiss thousands separator, e.g. "12'500 kg"."""
    return f"{kg:,.0f} kg".replace(",", "'")


@dataclass(frozen=True)
class WeekVolume:
    week_start: date  # Monday
    sets: int
    tonnage_kg: float  # sum of weight × reps; bodyweight sets count as sets only


def weekly_volume(conn: sqlite3.Connection) -> list[WeekVolume]:
    """Sets and tonnage per calendar week, oldest first, including weeks without training."""
    rows = conn.execute(
        "SELECT w.date, s.reps, s.weight_kg FROM workout_set s"
        " JOIN workout w ON w.id = s.workout_id"
    ).fetchall()
    if not rows:
        return []

    sets: dict[date, int] = {}
    tonnage: dict[date, float] = {}
    for iso_date, reps, weight_kg in rows:
        day = date.fromisoformat(iso_date)
        week = day - timedelta(days=day.weekday())
        sets[week] = sets.get(week, 0) + 1
        tonnage[week] = tonnage.get(week, 0) + (weight_kg or 0) * reps

    weeks = []
    week, last = min(sets), max(sets)
    while week <= last:
        weeks.append(WeekVolume(week, sets.get(week, 0), tonnage.get(week, 0)))
        week += timedelta(weeks=1)
    return weeks


def progress_label(conn: sqlite3.Connection, exercise_id: int) -> str | None:
    """First → best, e.g. "75 → 85 kg"; reps for bodyweight-only exercises, e.g. "BW × 6 → BW × 9".

    None if the exercise was never logged.
    """
    weighted = _weighted_sets(conn, exercise_id)
    if weighted:
        first = weighted[0][1].weight_kg
        best = max(s.weight_kg for _, s in weighted)
        if first == best:
            return f"{format_weight(best)} kg"
        return f"{format_weight(first)} → {format_weight(best)} kg"

    rows = conn.execute(
        "SELECT s.reps FROM workout_set s JOIN workout w ON w.id = s.workout_id"
        " WHERE s.exercise_id = ? ORDER BY w.date, s.id",
        (exercise_id,),
    ).fetchall()
    if not rows:
        return None
    first, best = rows[0][0], max(r for (r,) in rows)
    return f"BW × {best}" if first == best else f"BW × {first} → BW × {best}"
