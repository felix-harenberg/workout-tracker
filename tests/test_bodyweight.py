import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import bodyweight as bw
from core.db import MIGRATIONS, connect


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


# --- Logging ---


def test_no_weights_yet(conn: sqlite3.Connection) -> None:
    assert bw.list_weights(conn) == []
    assert bw.latest_weight(conn) is None


def test_log_and_list_oldest_first(conn: sqlite3.Connection) -> None:
    bw.log_weight(conn, date(2026, 10, 19), 78.7)
    bw.log_weight(conn, date(2026, 10, 12), 79.0)
    bw.log_weight(conn, date(2026, 10, 26), 78.4)

    assert bw.list_weights(conn) == [
        (date(2026, 10, 12), 79.0),
        (date(2026, 10, 19), 78.7),
        (date(2026, 10, 26), 78.4),
    ]
    assert bw.latest_weight(conn) == (date(2026, 10, 26), 78.4)


def test_second_entry_on_the_same_day_replaces_the_first(conn: sqlite3.Connection) -> None:
    bw.log_weight(conn, date(2026, 10, 26), 78.4)
    bw.log_weight(conn, date(2026, 10, 26), 78.2)
    assert bw.list_weights(conn) == [(date(2026, 10, 26), 78.2)]


def test_list_weights_since(conn: sqlite3.Connection) -> None:
    bw.log_weight(conn, date(2026, 9, 1), 80.0)
    bw.log_weight(conn, date(2026, 10, 1), 79.0)
    assert bw.list_weights(conn, since=date(2026, 9, 15)) == [(date(2026, 10, 1), 79.0)]


@pytest.mark.parametrize("kg", [0, -1])
def test_log_weight_rejects_non_positive(conn: sqlite3.Connection, kg: float) -> None:
    with pytest.raises(ValueError):
        bw.log_weight(conn, date(2026, 10, 26), kg)


def test_delete_weight(conn: sqlite3.Connection) -> None:
    bw.log_weight(conn, date(2026, 10, 26), 78.4)
    bw.delete_weight(conn, date(2026, 10, 26))
    assert bw.list_weights(conn) == []


# --- Goal ---


def test_goal_is_none_by_default(conn: sqlite3.Connection) -> None:
    assert bw.get_goal(conn) is None


def test_set_change_and_clear_goal(conn: sqlite3.Connection) -> None:
    bw.set_goal(conn, 75.0)
    assert bw.get_goal(conn) == 75.0
    bw.set_goal(conn, 76.5)
    assert bw.get_goal(conn) == 76.5
    bw.set_goal(conn, None)
    assert bw.get_goal(conn) is None


@pytest.mark.parametrize(
    ("current", "goal", "text"),
    [
        (78.4, 75.0, "noch 3.4 kg bis Ziel"),  # losing weight
        (68.0, 72.5, "noch 4.5 kg bis Ziel"),  # gaining weight
        (75.04, 75.0, "Ziel erreicht"),
        (78.4, None, "Kein Ziel gesetzt"),
    ],
)
def test_goal_label(current: float, goal: float | None, text: str) -> None:
    assert bw.goal_label(current, goal) == text


# --- Ranges and stepping ---


@pytest.mark.parametrize(
    ("period", "start"),
    [
        ("1M", date(2026, 9, 26)),
        ("3M", date(2026, 7, 26)),
        ("1J", date(2025, 10, 26)),
        ("Alles", None),
    ],
)
def test_period_start(period: str, start: date | None) -> None:
    assert bw.period_start(period, today=date(2026, 10, 26)) == start


def test_period_start_end_of_month() -> None:
    assert bw.period_start("1M", today=date(2026, 3, 31)) == date(2026, 2, 28)


@pytest.mark.parametrize(
    ("text", "delta", "result"),
    [
        ("78.4", 0.1, "78.5"),
        ("78,4", -0.5, "77.9"),
        ("78.3", 0.1, "78.4"),  # no float noise like 78.39999
        ("80", 0.5, "80.5"),
        ("abc", 0.1, "abc"),
    ],
)
def test_step_bodyweight(text: str, delta: float, result: str) -> None:
    assert bw.step_bodyweight(text, delta) == result


# --- Migration and export ---


def test_v3_database_gets_bodyweight_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "v3.db"
    old = sqlite3.connect(db_path)
    for script in MIGRATIONS[:3]:
        old.executescript(script)
    old.executescript("INSERT INTO exercise (name) VALUES ('Bench'); PRAGMA user_version = 3;")
    old.close()

    conn = connect(db_path)
    bw.log_weight(conn, date(2026, 10, 26), 78.4)
    assert bw.latest_weight(conn) == (date(2026, 10, 26), 78.4)
    assert conn.execute("SELECT name FROM exercise").fetchone() == ("Bench",)
    conn.close()


def test_export_bodyweight_csv(conn: sqlite3.Connection) -> None:
    bw.log_weight(conn, date(2026, 10, 19), 78.7)
    bw.log_weight(conn, date(2026, 10, 26), 78.4)
    assert bw.export_bodyweight_csv(conn).splitlines() == [
        "date,weight_kg",
        "2026-10-19,78.7",
        "2026-10-26,78.4",
    ]
