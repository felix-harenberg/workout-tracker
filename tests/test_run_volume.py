import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import run_volume as rv
from core.db import MIGRATIONS, connect

MONDAY = date(2026, 11, 2)


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


@pytest.mark.parametrize(
    "day", [date(2026, 11, 2), date(2026, 11, 5), date(2026, 11, 8)]
)  # Monday, Thursday, Sunday
def test_week_starts_on_monday(day: date) -> None:
    assert rv.week_start(day) == MONDAY


# --- Runs ---


def test_runs_add_up_per_week(conn: sqlite3.Connection) -> None:
    rv.add_run(conn, date(2026, 11, 1), 10)  # Sunday before: other week
    rv.add_run(conn, date(2026, 11, 3), 5.5)
    rv.add_run(conn, date(2026, 11, 8), 7)  # Sunday: same week

    assert rv.week_km(conn, MONDAY) == 12.5
    assert [r.distance_km for r in rv.runs_in_week(conn, MONDAY)] == [5.5, 7]


def test_update_and_delete_run(conn: sqlite3.Connection) -> None:
    run = rv.add_run(conn, date(2026, 11, 3), 5)
    rv.update_run(conn, run.id, date(2026, 11, 4), 6.5)
    assert rv.runs_in_week(conn, MONDAY) == [rv.RunEntry(run.id, date(2026, 11, 4), 6.5)]

    rv.delete_run(conn, run.id)
    assert rv.week_km(conn, MONDAY) == 0


def test_distance_must_be_positive(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        rv.add_run(conn, MONDAY, 0)


@pytest.mark.parametrize(("text", "km"), [("5", 5.0), ("7,5", 7.5), (" 10.25 ", 10.25)])
def test_parse_km(text: str, km: float) -> None:
    assert rv.parse_km(text) == km


@pytest.mark.parametrize("text", ["", None, "0", "-3", "abc"])
def test_parse_km_rejects(text: str | None) -> None:
    with pytest.raises(ValueError):
        rv.parse_km(text)


@pytest.mark.parametrize(
    ("text", "delta", "result"),
    [("5", 1, "6"), ("5", -0.5, "4.5"), ("0.5", -1, "0.5"), ("", 1, "1"), ("x", 1, "x")],
)
def test_step_km(text: str, delta: float, result: str) -> None:
    assert rv.step_km(text, delta) == result


# --- Goals ---


def test_goal_per_week(conn: sqlite3.Connection) -> None:
    assert rv.get_goal(conn, MONDAY) is None
    rv.set_goal(conn, date(2026, 11, 5), 22)  # any day of the week
    assert rv.get_goal(conn, MONDAY) == 22
    assert rv.get_goal(conn, date(2026, 11, 9)) is None


def test_first_suggestion_is_20(conn: sqlite3.Connection) -> None:
    assert rv.suggest_goal(conn, MONDAY) == 20


@pytest.mark.parametrize(("last", "suggested"), [(20, 22), (22, 24), (24, 26.5), (30, 33)])
def test_suggestion_is_last_goal_plus_10_percent(
    conn: sqlite3.Connection, last: float, suggested: float
) -> None:
    rv.set_goal(conn, date(2026, 10, 19), last)  # two weeks back: a skipped week is fine
    rv.set_goal(conn, date(2026, 11, 16), 50)  # later weeks don't count
    assert rv.suggest_goal(conn, MONDAY) == suggested


@pytest.mark.parametrize(
    ("km", "goal", "text"),
    [
        (12.5, 22, "noch 9.5 km"),
        (22, 22, "Ziel erreicht"),
        (25, 22, "Ziel erreicht · +3 km"),
        (5, None, "Kein Ziel gesetzt"),
    ],
)
def test_goal_label(km: float, goal: float | None, text: str) -> None:
    assert rv.goal_label(km, goal) == text


# --- History ---


def test_history_includes_empty_weeks(conn: sqlite3.Connection) -> None:
    rv.set_goal(conn, date(2026, 10, 19), 20)
    rv.add_run(conn, date(2026, 10, 20), 8)
    rv.add_run(conn, date(2026, 11, 3), 5)

    history = rv.history(conn, today=date(2026, 11, 5))

    assert history == [
        rv.WeekKm(date(2026, 10, 19), 8, 20),
        rv.WeekKm(date(2026, 10, 26), 0, None),
        rv.WeekKm(date(2026, 11, 2), 5, None),
    ]


def test_history_is_limited(conn: sqlite3.Connection) -> None:
    rv.add_run(conn, date(2026, 1, 5), 8)
    history = rv.history(conn, today=date(2026, 11, 5), weeks=4)
    assert [w.week for w in history] == [
        date(2026, 10, 12),
        date(2026, 10, 19),
        date(2026, 10, 26),
        date(2026, 11, 2),
    ]


def test_no_history_without_runs_or_goals(conn: sqlite3.Connection) -> None:
    assert rv.history(conn, today=MONDAY) == []


# --- Export and migration ---


def test_export_runs_csv(conn: sqlite3.Connection) -> None:
    rv.add_run(conn, date(2026, 11, 3), 5.5)
    rv.add_run(conn, date(2026, 11, 1), 10)
    rv.set_goal(conn, MONDAY, 22)

    assert rv.export_runs_csv(conn).splitlines() == [
        "date,distance_km,week_goal_km",
        "2026-11-01,10,",
        "2026-11-03,5.5,22",
    ]


def test_v7_database_gets_run_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "v7.db"
    old = sqlite3.connect(db_path)
    for script in MIGRATIONS[:7]:
        old.executescript(script)
    old.executescript("PRAGMA user_version = 7;")
    old.close()

    conn = connect(db_path)
    assert rv.week_km(conn, MONDAY) == 0
    conn.close()
