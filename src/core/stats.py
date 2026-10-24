"""Progress stats: estimated 1RM, personal records, weekly volume and pace history."""

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from core.models import WorkoutSet
from core.run import pace_s_per_km

_SET_COLUMNS = "s.id, s.workout_id, s.exercise_id, s.set_number, s.reps, s.weight_kg"


def estimate_1rm(weight_kg: float, reps: int) -> float:
    """Estimated one-rep max (Epley formula)."""
    if reps == 1:
        return weight_kg
    return weight_kg * (1 + reps / 30)


def format_1rm(value_kg: float) -> str:
    """Rounded to 0.5 kg, e.g. "101.5 kg"."""
    return f"{round(value_kg * 2) / 2:g} kg"


@dataclass(frozen=True)
class ExercisePR:
    best_1rm: float
    best_1rm_set: WorkoutSet
    best_1rm_date: date
    heaviest_set: WorkoutSet
    heaviest_date: date


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
    """Best estimated 1RM and heaviest set (ties go to more reps). None without weighted sets."""
    sets = _weighted_sets(conn, exercise_id)
    if not sets:
        return None
    best_date, best = max(sets, key=lambda ds: estimate_1rm(ds[1].weight_kg, ds[1].reps))
    heavy_date, heaviest = max(sets, key=lambda ds: (ds[1].weight_kg, ds[1].reps))
    return ExercisePR(
        best_1rm=estimate_1rm(best.weight_kg, best.reps),
        best_1rm_set=best,
        best_1rm_date=best_date,
        heaviest_set=heaviest,
        heaviest_date=heavy_date,
    )


def exercise_1rm_history(conn: sqlite3.Connection, exercise_id: int) -> list[tuple[date, float]]:
    """Best estimated 1RM per training day, oldest first."""
    best_per_day: dict[date, float] = {}
    for day, workout_set in _weighted_sets(conn, exercise_id):
        value = estimate_1rm(workout_set.weight_kg, workout_set.reps)
        best_per_day[day] = max(value, best_per_day.get(day, 0))
    return sorted(best_per_day.items())


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


def pace_history(conn: sqlite3.Connection) -> list[tuple[date, float]]:
    """Pace in seconds per km of every run, oldest first."""
    rows = conn.execute(
        "SELECT w.date, r.distance_km, r.duration_s FROM run r"
        " JOIN workout w ON w.id = r.workout_id ORDER BY w.date, w.id"
    ).fetchall()
    return [
        (date.fromisoformat(iso_date), pace_s_per_km(distance_km, duration_s))
        for iso_date, distance_km, duration_s in rows
    ]
