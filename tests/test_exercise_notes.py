import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core.db import MIGRATIONS, connect
from core.export import export_csv


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


def test_no_notes_by_default(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench")
    assert repo.get_exercise_notes(conn, bench.id) == ""


def test_notes_are_saved_per_exercise(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench")
    dips = repo.get_or_create_exercise(conn, "Dips")
    repo.set_exercise_notes(conn, bench.id, "Sitz auf Stufe 4\nenger Griff")

    assert repo.get_exercise_notes(conn, bench.id) == "Sitz auf Stufe 4\nenger Griff"
    assert repo.get_exercise_notes(conn, dips.id) == ""


def test_notes_are_trimmed_and_can_be_cleared(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench")
    repo.set_exercise_notes(conn, bench.id, "  enger Griff \n")
    assert repo.get_exercise_notes(conn, bench.id) == "enger Griff"

    repo.set_exercise_notes(conn, bench.id, "   ")
    assert repo.get_exercise_notes(conn, bench.id) == ""


def test_notes_survive_deleting_the_exercise_from_a_workout(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench")
    workout = repo.create_workout(conn, "Chest", date(2026, 11, 2))
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    repo.set_exercise_notes(conn, bench.id, "enger Griff")

    repo.delete_exercise_from_workout(conn, workout.id, bench.id)

    assert repo.get_exercise_notes(conn, bench.id) == "enger Griff"


def test_notes_in_csv_export(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench")
    workout = repo.create_workout(conn, "Chest", date(2026, 11, 2))
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=80)
    repo.set_exercise_notes(conn, bench.id, "enger Griff")

    header, row = export_csv(conn).splitlines()
    columns = dict(zip(header.split(","), row.split(","), strict=True))
    assert columns["exercise_notes"] == "enger Griff"


def test_v4_database_gets_notes_column(tmp_path: Path) -> None:
    db_path = tmp_path / "v4.db"
    old = sqlite3.connect(db_path)
    for script in MIGRATIONS[:4]:
        old.executescript(script)
    old.executescript(
        "INSERT INTO exercise (id, name) VALUES (1, 'Bench'); PRAGMA user_version = 4;"
    )
    old.close()

    conn = connect(db_path)
    assert repo.get_exercise_notes(conn, 1) == ""
    conn.close()
