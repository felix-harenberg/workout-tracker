"""Repeat a previous workout: pick it as a template and see its exercises again."""

import sqlite3
from dataclasses import dataclass
from datetime import date

from core import repository as repo
from core.models import Exercise, Workout, WorkoutSet, WorkoutType
from core.training import group_sets_by_exercise


@dataclass(frozen=True)
class WorkoutTemplate:
    name: str  # spelling of the latest workout with this name
    last_date: date
    workout_id: int
    exercise_count: int


@dataclass(frozen=True)
class PendingExercise:
    exercise: Exercise
    last_sets: list[WorkoutSet]


def _key(name: str) -> str:
    return name.strip().casefold()


def workout_templates(conn: sqlite3.Connection, today: date | None = None) -> list[WorkoutTemplate]:
    """The latest logged strength workout per name, newest first.

    Names match ignoring case and surrounding spaces. Unnamed workouts, workouts without
    sets and workouts dated after `today` are skipped: a future workout can't be "last
    time", and pending_exercises would find nothing for it.
    """
    today = today or date.today()
    result: dict[str, WorkoutTemplate] = {}
    for workout in repo.list_workouts(conn):
        key = _key(workout.name)
        if not key or key in result or workout.type != WorkoutType.STRENGTH:
            continue
        if workout.date > today:
            continue
        sets = repo.list_sets(conn, workout.id)
        if not sets:
            continue
        result[key] = WorkoutTemplate(
            name=workout.name.strip(),
            last_date=workout.date,
            workout_id=workout.id,
            exercise_count=len({s.exercise_id for s in sets}),
        )
    return list(result.values())


def pending_exercises(conn: sqlite3.Connection, workout: Workout) -> list[PendingExercise]:
    """Exercises of the previous workout with the same name that are not logged yet.

    In the order they were done last time, each with last time's sets.
    """
    key = _key(workout.name)
    if not key:
        return []

    previous = next(
        (
            w
            for w in repo.list_workouts(conn)  # newest first
            if _key(w.name) == key
            and (w.date, w.id) < (workout.date, workout.id)
            and repo.list_sets(conn, w.id)
        ),
        None,
    )
    if previous is None:
        return []

    done_today = {s.exercise_id for s in repo.list_sets(conn, workout.id)}
    pending = []
    for exercise_id, sets in group_sets_by_exercise(repo.list_sets(conn, previous.id)):
        if exercise_id in done_today:
            continue
        exercise = repo.get_exercise(conn, exercise_id)
        assert exercise is not None
        pending.append(PendingExercise(exercise=exercise, last_sets=sets))
    return pending


def copy_pending_exercises(conn: sqlite3.Connection, workout: Workout) -> int:
    """Log every exercise still pending from last time with all of last time's sets.

    Exercises already logged today are left alone. Returns the number of sets added.
    """
    added = 0
    for pending in pending_exercises(conn, workout):
        for s in pending.last_sets:
            repo.add_set(conn, workout.id, s.exercise_id, reps=s.reps, weight_kg=s.weight_kg)
            added += 1
    return added


def copy_missing_sets(conn: sqlite3.Connection, workout: Workout, exercise_id: int) -> int:
    """Log the sets of last time that are still missing today for one exercise.

    With 1 set done today and 3 last time, sets 2 and 3 are added. Returns the count.
    """
    last = repo.last_sets_for_exercise(conn, exercise_id, before=workout)
    if last is None:
        return 0
    done = [s for s in repo.list_sets(conn, workout.id) if s.exercise_id == exercise_id]
    missing = last[1][len(done) :]
    for s in missing:
        repo.add_set(conn, workout.id, exercise_id, reps=s.reps, weight_kg=s.weight_kg)
    return len(missing)
