import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core.db import MIGRATIONS, connect
from core.models import Hint, WeightHint
from core.training import hint_message


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


def setup(conn: sqlite3.Connection):
    bench = repo.get_or_create_exercise(conn, "Bench")
    today = repo.create_workout(conn, "Chest", date(2026, 10, 22))
    repo.add_set(conn, today.id, bench.id, reps=8, weight_kg=80)
    return bench, today


def test_no_hint_by_default(conn: sqlite3.Connection) -> None:
    bench, _ = setup(conn)
    assert repo.get_hint(conn, bench.id) is None


def test_set_and_get_hint(conn: sqlite3.Connection) -> None:
    bench, today = setup(conn)
    repo.set_hint(conn, bench.id, today.id, Hint.UP)

    hint = repo.get_hint(conn, bench.id)

    assert hint is not None
    assert hint.direction == Hint.UP
    assert hint.workout_id == today.id
    assert hint.set_on == date(2026, 10, 22)


def test_set_hint_none_removes_it(conn: sqlite3.Connection) -> None:
    bench, today = setup(conn)
    repo.set_hint(conn, bench.id, today.id, Hint.DOWN)
    repo.set_hint(conn, bench.id, today.id, None)
    assert repo.get_hint(conn, bench.id) is None


def test_hint_survives_more_sets_in_the_same_workout(conn: sqlite3.Connection) -> None:
    bench, today = setup(conn)
    repo.set_hint(conn, bench.id, today.id, Hint.UP)
    repo.add_set(conn, today.id, bench.id, reps=8, weight_kg=80)
    assert repo.get_hint(conn, bench.id) is not None


def test_first_set_in_a_later_workout_uses_up_the_hint(conn: sqlite3.Connection) -> None:
    bench, today = setup(conn)
    repo.set_hint(conn, bench.id, today.id, Hint.UP)
    next_time = repo.create_workout(conn, "Chest", date(2026, 10, 29))

    assert repo.get_hint(conn, bench.id) is not None  # still shown before the first set
    repo.add_set(conn, next_time.id, bench.id, reps=8, weight_kg=82.5)
    assert repo.get_hint(conn, bench.id) is None


def test_set_of_another_exercise_keeps_the_hint(conn: sqlite3.Connection) -> None:
    bench, today = setup(conn)
    squat = repo.get_or_create_exercise(conn, "Squat")
    repo.set_hint(conn, bench.id, today.id, Hint.UP)
    next_time = repo.create_workout(conn, "Legs", date(2026, 10, 24))
    repo.add_set(conn, next_time.id, squat.id, reps=5, weight_kg=100)
    assert repo.get_hint(conn, bench.id) is not None


def test_hint_stays_when_its_workout_is_deleted(conn: sqlite3.Connection) -> None:
    bench, today = setup(conn)
    repo.set_hint(conn, bench.id, today.id, Hint.DOWN)
    repo.delete_workout(conn, today.id)

    hint = repo.get_hint(conn, bench.id)

    assert hint is not None
    assert hint.direction == Hint.DOWN
    assert hint.workout_id is None
    assert hint.set_on is None


def test_v2_database_gets_hint_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "v2.db"
    old = sqlite3.connect(db_path)
    old.executescript(MIGRATIONS[0])
    old.executescript(MIGRATIONS[1])
    old.executescript(
        "INSERT INTO exercise (id, name) VALUES (1, 'Bench'); PRAGMA user_version = 2;"
    )
    old.close()

    conn = connect(db_path)
    assert repo.get_exercise(conn, 1) is not None
    assert repo.get_hint(conn, 1) is None
    conn.close()


@pytest.mark.parametrize(
    ("direction", "set_on", "text"),
    [
        (Hint.UP, date(2026, 10, 22), "Mehr Gewicht hast du dir am Do · 22. Okt vorgenommen"),
        (Hint.DOWN, date(2026, 10, 25), "Weniger Gewicht hast du dir gestern vorgenommen"),
        (Hint.UP, None, "Mehr Gewicht hast du dir vorgenommen"),
    ],
)
def test_hint_message(direction: Hint, set_on: date | None, text: str) -> None:
    hint = WeightHint(direction=direction, workout_id=1, set_on=set_on)
    assert hint_message(hint, today=date(2026, 10, 26)) == text
