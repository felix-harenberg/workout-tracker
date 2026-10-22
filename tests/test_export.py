import csv
import io
import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core.db import connect
from core.export import CSV_COLUMNS, export_csv, export_filename


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


def read_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def test_empty_database_exports_header_only(conn: sqlite3.Connection) -> None:
    text = export_csv(conn)
    assert text.splitlines() == [",".join(CSV_COLUMNS)]


def test_one_row_per_set(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Chestday", date(2026, 10, 22), notes="good")
    bench = repo.get_or_create_exercise(conn, "Bankdrücken")
    dips = repo.get_or_create_exercise(conn, "Dips")
    repo.add_set(conn, workout.id, bench.id, reps=8, weight_kg=82.5)
    repo.add_set(conn, workout.id, dips.id, reps=12)

    rows = read_rows(export_csv(conn))

    assert rows == [
        {
            "workout_id": str(workout.id),
            "date": "2026-10-22",
            "workout_name": "Chestday",
            "workout_notes": "good",
            "exercise": "Bankdrücken",
            "set_number": "1",
            "reps": "8",
            "weight_kg": "82.5",
        },
        {
            "workout_id": str(workout.id),
            "date": "2026-10-22",
            "workout_name": "Chestday",
            "workout_notes": "good",
            "exercise": "Dips",
            "set_number": "1",
            "reps": "12",
            "weight_kg": "",
        },
    ]


def test_workout_without_sets_is_kept(conn: sqlite3.Connection) -> None:
    repo.create_workout(conn, "Empty", date(2026, 10, 22))
    rows = read_rows(export_csv(conn))
    assert len(rows) == 1
    assert rows[0]["workout_name"] == "Empty"
    assert rows[0]["exercise"] == rows[0]["reps"] == ""


def test_rows_sorted_oldest_workout_first(conn: sqlite3.Connection) -> None:
    bench = repo.get_or_create_exercise(conn, "Bench")
    new = repo.create_workout(conn, "new", date(2026, 10, 22))
    old = repo.create_workout(conn, "old", date(2026, 10, 1))
    repo.add_set(conn, new.id, bench.id, reps=8, weight_kg=80)
    repo.add_set(conn, old.id, bench.id, reps=8, weight_kg=75)
    repo.add_set(conn, old.id, bench.id, reps=6, weight_kg=77.5)

    rows = read_rows(export_csv(conn))
    assert [(r["workout_name"], r["set_number"]) for r in rows] == [
        ("old", "1"),
        ("old", "2"),
        ("new", "1"),
    ]


def test_notes_with_commas_and_newlines_survive(conn: sqlite3.Connection) -> None:
    repo.create_workout(conn, "x", date(2026, 10, 22), notes='tired, "heavy"\nsecond line')
    assert read_rows(export_csv(conn))[0]["workout_notes"] == 'tired, "heavy"\nsecond line'


def test_export_filename() -> None:
    assert export_filename(date(2026, 10, 22)) == "workout-tracker-2026-10-22.csv"
