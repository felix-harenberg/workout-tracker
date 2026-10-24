import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core.db import MIGRATIONS, SCHEMA_VERSION, connect
from core.models import WorkoutType


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


# --- Schema ---


def test_connect_sets_schema_version(conn: sqlite3.Connection) -> None:
    assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION


def test_connect_twice_keeps_data(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    first = connect(db_path)
    repo.get_or_create_exercise(first, "Squat")
    first.close()

    second = connect(db_path)
    assert [e.name for e in repo.list_exercises(second)] == ["Squat"]
    second.close()


def test_connect_creates_missing_parent_directory(tmp_path: Path) -> None:
    connection = connect(tmp_path / "nested" / "test.db")
    assert repo.list_exercises(connection) == []
    connection.close()


# --- Exercises ---


def test_get_or_create_exercise_creates_new(conn: sqlite3.Connection) -> None:
    exercise = repo.get_or_create_exercise(conn, "Bench Press")
    assert exercise.id is not None
    assert exercise.name == "Bench Press"


def test_get_or_create_exercise_strips_whitespace(conn: sqlite3.Connection) -> None:
    assert repo.get_or_create_exercise(conn, "  Deadlift ").name == "Deadlift"


def test_get_or_create_exercise_ignores_case(conn: sqlite3.Connection) -> None:
    first = repo.get_or_create_exercise(conn, "Bankdrücken")
    second = repo.get_or_create_exercise(conn, "BANKDRÜCKEN")
    assert second == first
    assert len(repo.list_exercises(conn)) == 1


def test_get_or_create_exercise_rejects_empty_name(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        repo.get_or_create_exercise(conn, "   ")


def test_list_exercises_sorted_by_name(conn: sqlite3.Connection) -> None:
    for name in ["squat", "Bench Press", "Deadlift"]:
        repo.get_or_create_exercise(conn, name)
    assert [e.name for e in repo.list_exercises(conn)] == ["Bench Press", "Deadlift", "squat"]


# --- Workouts ---


def test_create_and_get_workout(conn: sqlite3.Connection) -> None:
    created = repo.create_workout(conn, "Chest Day", date(2026, 10, 22), notes="felt strong")
    loaded = repo.get_workout(conn, created.id)
    assert loaded == created
    assert loaded.date == date(2026, 10, 22)
    assert loaded.notes == "felt strong"


def test_create_workout_defaults_to_empty_notes(conn: sqlite3.Connection) -> None:
    assert repo.create_workout(conn, "Leg Day", date(2026, 10, 22)).notes == ""


def test_get_workout_returns_none_for_unknown_id(conn: sqlite3.Connection) -> None:
    assert repo.get_workout(conn, 999) is None


def test_list_workouts_newest_first(conn: sqlite3.Connection) -> None:
    repo.create_workout(conn, "old", date(2026, 10, 1))
    repo.create_workout(conn, "new", date(2026, 10, 20))
    repo.create_workout(conn, "same day, later", date(2026, 10, 20))
    assert [w.name for w in repo.list_workouts(conn)] == ["same day, later", "new", "old"]


# --- Sets ---


def test_add_set_numbers_sets_per_exercise(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    dips = repo.get_or_create_exercise(conn, "Dips")

    first = repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    second = repo.add_set(conn, workout.id, bench.id, reps=6, weight_kg=85)
    other = repo.add_set(conn, workout.id, dips.id, reps=12)

    assert (first.set_number, second.set_number, other.set_number) == (1, 2, 1)


def test_set_numbers_restart_in_new_workout(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    monday = repo.create_workout(conn, "Mon", date(2026, 10, 19))
    thursday = repo.create_workout(conn, "Thu", date(2026, 10, 22))
    repo.add_set(conn, monday.id, bench.id, reps=8, weight_kg=80)
    assert repo.add_set(conn, thursday.id, bench.id, reps=8, weight_kg=80).set_number == 1


def test_add_set_stores_decimal_weight(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    repo.add_set(conn, workout.id, bench.id, reps=5, weight_kg=82.5)
    assert repo.list_sets(conn, workout.id)[0].weight_kg == 82.5


def test_set_without_weight_is_bodyweight(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Pull", date(2026, 10, 22))
    pullups = repo.get_or_create_exercise(conn, "Pull-ups")
    loaded = repo.add_set(conn, workout.id, pullups.id, reps=10)
    assert loaded.weight_kg is None
    assert loaded.is_bodyweight


def test_set_with_weight_is_not_bodyweight(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    assert not repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80).is_bodyweight


@pytest.mark.parametrize(("reps", "weight_kg"), [(0, 80), (-1, 80), (8, -5)])
def test_add_set_rejects_invalid_values(
    conn: sqlite3.Connection, reps: int, weight_kg: float
) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    with pytest.raises(ValueError):
        repo.add_set(conn, workout.id, bench.id, reps=reps, weight_kg=weight_kg)


def test_add_set_rejects_unknown_workout(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    with pytest.raises(sqlite3.IntegrityError):
        repo.add_set(conn, 999, bench.id, reps=8, weight_kg=80)


def test_list_sets_in_logged_order(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    dips = repo.get_or_create_exercise(conn, "Dips")
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, workout.id, dips.id, reps=12)
    repo.add_set(conn, workout.id, bench.id, reps=6, weight_kg=85)

    sets = repo.list_sets(conn, workout.id)
    assert [(s.exercise_id, s.set_number) for s in sets] == [
        (bench.id, 1),
        (dips.id, 1),
        (bench.id, 2),
    ]


def test_list_sets_only_returns_sets_of_that_workout(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    a = repo.create_workout(conn, "A", date(2026, 10, 19))
    b = repo.create_workout(conn, "B", date(2026, 10, 22))
    repo.add_set(conn, a.id, bench.id, reps=8, weight_kg=80)
    assert repo.list_sets(conn, b.id) == []


def test_get_exercise(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    assert repo.get_exercise(conn, bench.id) == bench
    assert repo.get_exercise(conn, 999) is None


# --- Last time ---


def test_last_sets_for_exercise_finds_most_recent_earlier_workout(
    conn: sqlite3.Connection,
) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    older = repo.create_workout(conn, "Chest", date(2026, 10, 8))
    last = repo.create_workout(conn, "Chest", date(2026, 10, 15))
    today = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    repo.add_set(conn, older.id, bench.id, reps=8, weight_kg=75)
    repo.add_set(conn, last.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, last.id, bench.id, reps=6, weight_kg=85)
    repo.add_set(conn, today.id, bench.id, reps=8, weight_kg=82.5)

    result = repo.last_sets_for_exercise(conn, bench.id, before=today)
    assert result is not None
    workout, sets = result
    assert workout == last
    assert [(s.weight_kg, s.reps) for s in sets] == [(80, 8), (85, 6)]


def test_last_sets_for_exercise_skips_workouts_without_that_exercise(
    conn: sqlite3.Connection,
) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    squat = repo.get_or_create_exercise(conn, "Squat")
    chest = repo.create_workout(conn, "Chest", date(2026, 10, 15))
    legs = repo.create_workout(conn, "Legs", date(2026, 10, 18))
    today = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    repo.add_set(conn, chest.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, legs.id, squat.id, reps=5, weight_kg=100)

    result = repo.last_sets_for_exercise(conn, bench.id, before=today)
    assert result is not None
    assert result[0] == chest


def test_last_sets_for_exercise_same_day_uses_earlier_workout(
    conn: sqlite3.Connection,
) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    morning = repo.create_workout(conn, "AM", date(2026, 10, 22))
    evening = repo.create_workout(conn, "PM", date(2026, 10, 22))
    repo.add_set(conn, morning.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, evening.id, bench.id, reps=8, weight_kg=60)

    result = repo.last_sets_for_exercise(conn, bench.id, before=evening)
    assert result is not None
    assert result[0] == morning
    assert repo.last_sets_for_exercise(conn, bench.id, before=morning) is None


def test_last_sets_for_exercise_none_when_never_done(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    today = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    assert repo.last_sets_for_exercise(conn, bench.id, before=today) is None


# --- Editing and deleting ---


def test_update_workout(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    updated = repo.update_workout(
        conn, workout.id, name="Chestday", workout_date=date(2026, 10, 21), notes="tired"
    )
    assert updated == repo.get_workout(conn, workout.id)
    assert (updated.name, updated.date, updated.notes) == ("Chestday", date(2026, 10, 21), "tired")


def test_update_unknown_workout_raises(conn: sqlite3.Connection) -> None:
    with pytest.raises(LookupError):
        repo.update_workout(conn, 999, name="x", workout_date=date(2026, 10, 22), notes="")


def test_delete_workout_removes_its_sets_but_keeps_exercises(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    workout = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    other = repo.create_workout(conn, "Chest", date(2026, 10, 15))
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, other.id, bench.id, reps=8, weight_kg=75)

    repo.delete_workout(conn, workout.id)

    assert repo.get_workout(conn, workout.id) is None
    assert conn.execute("SELECT COUNT(*) FROM workout_set").fetchone()[0] == 1
    assert repo.list_exercises(conn) == [bench]


def test_update_set(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    original = repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)

    updated = repo.update_set(conn, original.id, reps=6, weight_kg=None)

    assert updated == repo.list_sets(conn, workout.id)[0]
    assert (updated.set_number, updated.reps, updated.weight_kg) == (1, 6, None)


def test_update_set_rejects_invalid_values(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    original = repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    with pytest.raises(ValueError):
        repo.update_set(conn, original.id, reps=0, weight_kg=80)


def test_update_unknown_set_raises(conn: sqlite3.Connection) -> None:
    with pytest.raises(LookupError):
        repo.update_set(conn, 999, reps=8, weight_kg=80)


def test_delete_set_renumbers_later_sets_of_same_exercise(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    dips = repo.get_or_create_exercise(conn, "Dips")
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    second = repo.add_set(conn, workout.id, bench.id, reps=6, weight_kg=85)
    repo.add_set(conn, workout.id, dips.id, reps=12)
    repo.add_set(conn, workout.id, bench.id, reps=5, weight_kg=85)

    repo.delete_set(conn, second.id)

    sets = repo.list_sets(conn, workout.id)
    assert [(s.exercise_id, s.set_number, s.reps) for s in sets] == [
        (bench.id, 1, 8),
        (dips.id, 1, 12),
        (bench.id, 2, 5),
    ]


def test_add_set_after_delete_continues_numbering(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    first = repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, workout.id, bench.id, reps=6, weight_kg=85)
    repo.delete_set(conn, first.id)
    assert repo.add_set(conn, workout.id, bench.id, reps=5, weight_kg=85).set_number == 2


def test_delete_exercise_from_workout(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench Press")
    dips = repo.get_or_create_exercise(conn, "Dips")
    workout = repo.create_workout(conn, "Push", date(2026, 10, 22))
    other = repo.create_workout(conn, "Push", date(2026, 10, 15))
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, workout.id, bench.id, reps=6, weight_kg=85)
    repo.add_set(conn, workout.id, dips.id, reps=12)
    repo.add_set(conn, other.id, bench.id, reps=8, weight_kg=75)

    repo.delete_exercise_from_workout(conn, workout.id, bench.id)

    assert [s.exercise_id for s in repo.list_sets(conn, workout.id)] == [dips.id]
    assert len(repo.list_sets(conn, other.id)) == 1
    assert bench in repo.list_exercises(conn)


# --- Migrations ---


def test_v1_database_is_upgraded_without_data_loss(tmp_path: Path) -> None:
    """A database from v0.1 (schema version 1) on the phone must survive the update."""
    db_path = tmp_path / "v1.db"
    old = sqlite3.connect(db_path)
    old.executescript(MIGRATIONS[0])
    old.executescript(
        """
        INSERT INTO exercise (id, name) VALUES (1, 'Benchpress');
        INSERT INTO workout (id, name, date, notes) VALUES (1, 'Bench focus', '2026-10-22', 'ok');
        INSERT INTO workout_set (workout_id, exercise_id, set_number, reps, weight_kg)
            VALUES (1, 1, 1, 8, 80);
        PRAGMA user_version = 1;
        """
    )
    old.close()

    conn = connect(db_path)

    assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    workout = repo.get_workout(conn, 1)
    assert workout is not None
    assert (workout.name, workout.date, workout.notes) == ("Bench focus", date(2026, 10, 22), "ok")
    assert workout.type == WorkoutType.STRENGTH
    assert [(s.reps, s.weight_kg) for s in repo.list_sets(conn, 1)] == [(8, 80)]
    conn.close()


# --- Runs ---


def test_create_workout_defaults_to_strength(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    assert workout.type == WorkoutType.STRENGTH
    assert repo.get_run(conn, workout.id) is None


def test_create_and_get_run(conn: sqlite3.Connection) -> None:
    workout, run = repo.create_run(
        conn, "Easy run", date(2026, 10, 24), distance_km=10.5, duration_s=3150
    )
    assert workout.type == WorkoutType.RUN
    assert repo.get_workout(conn, workout.id) == workout
    assert repo.get_run(conn, workout.id) == run
    assert (run.distance_km, run.duration_s) == (10.5, 3150)


def test_create_run_rejects_invalid_values(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        repo.create_run(conn, "x", date(2026, 10, 24), distance_km=0, duration_s=600)
    with pytest.raises(ValueError):
        repo.create_run(conn, "x", date(2026, 10, 24), distance_km=5, duration_s=0)
    assert repo.list_workouts(conn) == []


def test_update_run(conn: sqlite3.Connection) -> None:
    workout, _ = repo.create_run(conn, "", date(2026, 10, 24), distance_km=5, duration_s=1500)
    updated = repo.update_run(conn, workout.id, distance_km=5.2, duration_s=1490)
    assert updated == repo.get_run(conn, workout.id)
    assert (updated.distance_km, updated.duration_s) == (5.2, 1490)


def test_delete_run_workout_removes_run(conn: sqlite3.Connection) -> None:
    workout, _ = repo.create_run(conn, "", date(2026, 10, 24), distance_km=5, duration_s=1500)
    repo.delete_workout(conn, workout.id)
    assert repo.get_run(conn, workout.id) is None
    assert conn.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0


def test_list_workouts_mixes_types(conn: sqlite3.Connection) -> None:
    repo.create_workout(conn, "Chest", date(2026, 10, 22))
    repo.create_run(conn, "Run", date(2026, 10, 24), distance_km=5, duration_s=1500)
    assert [w.type for w in repo.list_workouts(conn)] == [WorkoutType.RUN, WorkoutType.STRENGTH]
