import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core import templates
from core.db import connect
from core.models import Workout


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


def log(
    conn: sqlite3.Connection, name: str, day: date, *exercises: tuple[str, int, float | None]
) -> Workout:
    """Log a workout with one (exercise, reps, weight) set per entry."""
    workout = repo.create_workout(conn, name, day)
    for exercise, reps, weight_kg in exercises:
        exercise_id = repo.get_or_create_exercise(conn, exercise).id
        repo.add_set(conn, workout.id, exercise_id, reps=reps, weight_kg=weight_kg)
    return workout


# --- workout_templates ---


def test_templates_one_per_name_newest_first(conn: sqlite3.Connection) -> None:
    log(conn, "Chestday", date(2026, 10, 15), ("Bench", 8, 80))
    log(conn, "Legday", date(2026, 10, 18), ("Squat", 5, 100))
    latest_chest = log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 82.5), ("Dips", 10, None))

    result = templates.workout_templates(conn)

    assert [(t.name, t.last_date, t.exercise_count) for t in result] == [
        ("Chestday", date(2026, 10, 22), 2),
        ("Legday", date(2026, 10, 18), 1),
    ]
    assert result[0].workout_id == latest_chest.id


def test_templates_group_names_ignoring_case_and_spaces(conn: sqlite3.Connection) -> None:
    log(conn, "chestday", date(2026, 10, 15), ("Bench", 8, 80))
    log(conn, " Chestday ", date(2026, 10, 22), ("Bench", 8, 80))
    result = templates.workout_templates(conn)
    assert len(result) == 1
    assert result[0].name == "Chestday"  # spelling of the latest workout


def test_templates_skip_unnamed_empty_and_run_workouts(conn: sqlite3.Connection) -> None:
    log(conn, "", date(2026, 10, 15), ("Bench", 8, 80))
    log(conn, "Empty", date(2026, 10, 16))
    repo.create_run(conn, "Easy run", date(2026, 10, 17), distance_km=5, duration_s=1500)
    assert templates.workout_templates(conn) == []


def test_template_ignores_newer_empty_workout_with_same_name(conn: sqlite3.Connection) -> None:
    done = log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80))
    log(conn, "Chestday", date(2026, 10, 26))  # just started, nothing logged yet
    (template,) = templates.workout_templates(conn)
    assert template.workout_id == done.id


# --- pending_exercises ---


def test_pending_exercises_from_last_workout_with_same_name(conn: sqlite3.Connection) -> None:
    log(conn, "Chestday", date(2026, 10, 15), ("Flys", 12, 20))
    log(
        conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80), ("Bench", 6, 85), ("Dips", 10, None)
    )
    today = repo.create_workout(conn, "Chestday", date(2026, 10, 26))

    pending = templates.pending_exercises(conn, today)

    assert [(p.exercise.name, [(s.weight_kg, s.reps) for s in p.last_sets]) for p in pending] == [
        ("Bench", [(80, 8), (85, 6)]),
        ("Dips", [(None, 10)]),
    ]


def test_pending_exercises_drop_once_logged_today(conn: sqlite3.Connection) -> None:
    log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80), ("Dips", 10, None))
    today = log(conn, "Chestday", date(2026, 10, 26), ("Bench", 8, 82.5))
    assert [p.exercise.name for p in templates.pending_exercises(conn, today)] == ["Dips"]


def test_pending_exercises_match_name_ignoring_case(conn: sqlite3.Connection) -> None:
    log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80))
    today = repo.create_workout(conn, "chestday", date(2026, 10, 26))
    assert len(templates.pending_exercises(conn, today)) == 1


def test_pending_exercises_empty_without_name_or_history(conn: sqlite3.Connection) -> None:
    log(conn, "", date(2026, 10, 22), ("Bench", 8, 80))
    unnamed = repo.create_workout(conn, "", date(2026, 10, 26))
    new_name = repo.create_workout(conn, "Armday", date(2026, 10, 26))
    assert templates.pending_exercises(conn, unnamed) == []
    assert templates.pending_exercises(conn, new_name) == []


def test_pending_exercises_only_look_at_earlier_workouts(conn: sqlite3.Connection) -> None:
    first = log(conn, "Chestday", date(2026, 10, 15), ("Bench", 8, 80))
    log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 82.5), ("Dips", 10, None))
    assert templates.pending_exercises(conn, first) == []


# --- Copying last time's sets ---


def sets_of(conn: sqlite3.Connection, workout: Workout) -> list[tuple[str, float | None, int]]:
    names = {e.id: e.name for e in repo.list_exercises(conn)}
    return [(names[s.exercise_id], s.weight_kg, s.reps) for s in repo.list_sets(conn, workout.id)]


def test_copy_pending_exercises_takes_all_sets_from_last_time(conn: sqlite3.Connection) -> None:
    log(
        conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80), ("Bench", 6, 85), ("Dips", 10, None)
    )
    today = repo.create_workout(conn, "Chestday", date(2026, 10, 28))

    copied = templates.copy_pending_exercises(conn, today)

    assert copied == 3
    assert sets_of(conn, today) == [("Bench", 80, 8), ("Bench", 85, 6), ("Dips", None, 10)]
    assert templates.pending_exercises(conn, today) == []


def test_copy_pending_exercises_keeps_what_was_logged_today(conn: sqlite3.Connection) -> None:
    log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80), ("Dips", 10, None))
    today = log(conn, "Chestday", date(2026, 10, 28), ("Bench", 8, 82.5))

    assert templates.copy_pending_exercises(conn, today) == 1
    assert sets_of(conn, today) == [("Bench", 82.5, 8), ("Dips", None, 10)]


def test_copy_pending_exercises_without_history_copies_nothing(conn: sqlite3.Connection) -> None:
    today = repo.create_workout(conn, "Armday", date(2026, 10, 28))
    assert templates.copy_pending_exercises(conn, today) == 0


def test_copy_missing_sets_of_one_exercise(conn: sqlite3.Connection) -> None:
    log(
        conn,
        "Chestday",
        date(2026, 10, 22),
        ("Bench", 8, 80),
        ("Bench", 8, 80),
        ("Bench", 6, 85),
        ("Dips", 10, None),
    )
    today = log(conn, "Chestday", date(2026, 10, 28), ("Bench", 8, 82.5))
    bench = repo.get_or_create_exercise(conn, "Bench")

    copied = templates.copy_missing_sets(conn, today, bench.id)

    assert copied == 2  # sets 2 and 3; set 1 was done today
    assert sets_of(conn, today) == [("Bench", 82.5, 8), ("Bench", 80, 8), ("Bench", 85, 6)]
    assert [s.set_number for s in repo.list_sets(conn, today.id)] == [1, 2, 3]


def test_copy_missing_sets_uses_last_time_of_the_exercise_in_any_workout(
    conn: sqlite3.Connection,
) -> None:
    log(conn, "Upper", date(2026, 10, 20), ("Bench", 5, 90))
    today = repo.create_workout(conn, "Chestday", date(2026, 10, 28))
    bench = repo.get_or_create_exercise(conn, "Bench")
    assert templates.copy_missing_sets(conn, today, bench.id) == 1
    assert sets_of(conn, today) == [("Bench", 90, 5)]


def test_copy_missing_sets_when_nothing_is_missing(conn: sqlite3.Connection) -> None:
    log(conn, "Chestday", date(2026, 10, 22), ("Bench", 8, 80))
    today = log(conn, "Chestday", date(2026, 10, 28), ("Bench", 8, 82.5))
    bench = repo.get_or_create_exercise(conn, "Bench")
    assert templates.copy_missing_sets(conn, today, bench.id) == 0


def test_templates_ignore_workouts_dated_in_the_future(conn: sqlite3.Connection) -> None:
    """A future workout can't be "last time"; the template list follows the same rule as
    pending_exercises, so picking a template never leads to an empty workout."""
    log(conn, "Deadlift Focus", date(2026, 10, 30), ("Deadlift", 5, 130))
    log(conn, "Bench Focus", date(2026, 10, 21), ("Bench", 8, 80))

    result = templates.workout_templates(conn, today=date(2026, 10, 28))

    assert [t.name for t in result] == ["Bench Focus"]
