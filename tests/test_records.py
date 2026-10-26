import random
import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core.db import connect
from core.records import QUOTES, check_new_set, pick_quote, suspicious_message


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


@pytest.fixture
def bench(conn: sqlite3.Connection) -> int:
    exercise = repo.get_or_create_exercise(conn, "Bench")
    workout = repo.create_workout(conn, "Chest", date(2026, 10, 15))
    repo.add_set(conn, workout.id, exercise.id, reps=8, weight_kg=80)
    repo.add_set(conn, workout.id, exercise.id, reps=8, weight_kg=82.5)
    return exercise.id


def test_heavier_than_ever_is_a_record(conn: sqlite3.Connection, bench: int) -> None:
    check = check_new_set(conn, bench, weight_kg=85)
    assert check.is_record
    assert not check.suspicious
    assert check.previous_best is not None
    assert (check.previous_best.weight_kg, check.previous_best.reps) == (82.5, 8)
    assert check.previous_date == date(2026, 10, 15)


@pytest.mark.parametrize("weight", [82.5, 80, 60])
def test_same_or_lighter_is_no_record(conn: sqlite3.Connection, bench: int, weight: float) -> None:
    check = check_new_set(conn, bench, weight_kg=weight)
    assert not check.is_record
    assert not check.suspicious


def test_more_than_20_percent_above_best_is_suspicious(
    conn: sqlite3.Connection, bench: int
) -> None:
    assert not check_new_set(conn, bench, weight_kg=99).suspicious  # exactly 20 %
    check = check_new_set(conn, bench, weight_kg=825)
    assert check.suspicious
    assert check.is_record


def test_first_set_of_an_exercise_is_no_record(conn: sqlite3.Connection) -> None:
    squat = repo.get_or_create_exercise(conn, "Squat")
    check = check_new_set(conn, squat.id, weight_kg=100)
    assert not check.is_record
    assert not check.suspicious
    assert check.previous_best is None


def test_bodyweight_set_is_no_record(conn: sqlite3.Connection, bench: int) -> None:
    check = check_new_set(conn, bench, weight_kg=None)
    assert not check.is_record
    assert not check.suspicious


@pytest.mark.parametrize(
    ("new", "old", "text"),
    [
        (825, 82.5, "Zehnmal so viel wie dein Bestwert. Vertippt, oder bist du jetzt einfach so?"),
        (170, 85, "Doppelt so viel wie dein Bestwert. Vertippt, oder bist du jetzt einfach so?"),
        (105, 82.5, "27 % mehr als dein Bestwert. Vertippt, oder bist du jetzt einfach so?"),
        (300, 100, "3-mal so viel wie dein Bestwert. Vertippt, oder bist du jetzt einfach so?"),
    ],
)
def test_suspicious_message(new: float, old: float, text: str) -> None:
    assert suspicious_message(new, old) == text


def test_pick_quote_is_one_of_the_quotes() -> None:
    rng = random.Random(1)
    assert {pick_quote(rng) for _ in range(50)} <= set(QUOTES)
    assert len({pick_quote(rng) for _ in range(50)}) > 1  # it actually varies
