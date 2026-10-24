import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core import stats
from core.db import connect


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


def log(
    conn: sqlite3.Connection, day: date, exercise: str, *sets: tuple[int, float | None]
) -> None:
    """Log one workout on `day` with (reps, weight_kg) sets of one exercise."""
    workout = repo.create_workout(conn, "", day)
    exercise_id = repo.get_or_create_exercise(conn, exercise).id
    for reps, weight_kg in sets:
        repo.add_set(conn, workout.id, exercise_id, reps=reps, weight_kg=weight_kg)


# --- estimate_1rm ---


@pytest.mark.parametrize(
    ("weight", "reps", "expected"),
    [(100, 1, 100), (80, 8, 80 * (1 + 8 / 30)), (90, 6, 108), (60, 10, 80)],
)
def test_estimate_1rm_epley(weight: float, reps: int, expected: float) -> None:
    assert stats.estimate_1rm(weight, reps) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "text"), [(108.0, "108 kg"), (101.33, "101.5 kg"), (100.2, "100 kg")]
)
def test_format_1rm_rounds_to_half_kg(value: float, text: str) -> None:
    assert stats.format_1rm(value) == text


# --- PRs ---


def test_exercise_pr(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Bench", (8, 80), (6, 85))
    log(conn, date(2026, 10, 8), "Bench", (6, 90), (3, 95))

    pr = stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Bench").id)

    assert pr is not None
    assert pr.best_1rm == pytest.approx(108)  # 90 × 6 beats 95 × 3 (104.5)
    assert (pr.best_1rm_set.weight_kg, pr.best_1rm_set.reps) == (90, 6)
    assert pr.best_1rm_date == date(2026, 10, 8)
    assert (pr.heaviest_set.weight_kg, pr.heaviest_set.reps) == (95, 3)
    assert pr.heaviest_date == date(2026, 10, 8)


def test_heaviest_tie_prefers_more_reps(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Bench", (3, 95))
    log(conn, date(2026, 10, 8), "Bench", (5, 95))
    pr = stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Bench").id)
    assert pr is not None
    assert pr.heaviest_set.reps == 5
    assert pr.heaviest_date == date(2026, 10, 8)


def test_exercise_pr_ignores_bodyweight_sets(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Pull-ups", (10, None))
    assert stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Pull-ups").id) is None


def test_exercise_pr_ignores_other_exercises(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Squat", (5, 140))
    log(conn, date(2026, 10, 1), "Bench", (5, 80))
    pr = stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Bench").id)
    assert pr is not None
    assert pr.heaviest_set.weight_kg == 80


# --- 1RM history ---


def test_1rm_history_best_set_per_day(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 8), "Bench", (6, 90), (3, 95))
    log(conn, date(2026, 10, 1), "Bench", (8, 80), (6, 85))
    log(conn, date(2026, 10, 5), "Pull-ups", (10, None))

    history = stats.exercise_1rm_history(conn, repo.get_or_create_exercise(conn, "Bench").id)

    assert [d for d, _ in history] == [date(2026, 10, 1), date(2026, 10, 8)]
    assert [round(v, 2) for _, v in history] == [round(85 * (1 + 6 / 30), 2), 108]


def test_1rm_history_two_workouts_same_day_merge(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Bench", (5, 80))
    log(conn, date(2026, 10, 1), "Bench", (5, 90))
    history = stats.exercise_1rm_history(conn, repo.get_or_create_exercise(conn, "Bench").id)
    assert len(history) == 1
    assert history[0][1] == pytest.approx(105)


# --- Weekly volume ---


def test_weekly_volume_counts_sets_and_tonnage(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 19), "Bench", (8, 80), (6, 85))  # Monday
    log(conn, date(2026, 10, 25), "Pull-ups", (10, None))  # Sunday, same week
    log(conn, date(2026, 10, 26), "Squat", (5, 100))  # next Monday

    weeks = stats.weekly_volume(conn)

    assert weeks == [
        stats.WeekVolume(week_start=date(2026, 10, 19), sets=3, tonnage_kg=8 * 80 + 6 * 85),
        stats.WeekVolume(week_start=date(2026, 10, 26), sets=1, tonnage_kg=500),
    ]


def test_weekly_volume_fills_weeks_without_training(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 5), "Bench", (5, 80))
    log(conn, date(2026, 10, 21), "Bench", (5, 80))
    weeks = stats.weekly_volume(conn)
    assert [(w.week_start, w.sets) for w in weeks] == [
        (date(2026, 10, 5), 1),
        (date(2026, 10, 12), 0),
        (date(2026, 10, 19), 1),
    ]


def test_weekly_volume_empty(conn: sqlite3.Connection) -> None:
    assert stats.weekly_volume(conn) == []


# --- Pace history ---


def test_pace_history_oldest_first(conn: sqlite3.Connection) -> None:
    repo.create_run(conn, "", date(2026, 10, 20), distance_km=10, duration_s=3000)
    repo.create_run(conn, "", date(2026, 10, 10), distance_km=5, duration_s=1650)
    repo.create_workout(conn, "Chest", date(2026, 10, 15))

    assert stats.pace_history(conn) == [(date(2026, 10, 10), 330), (date(2026, 10, 20), 300)]


@pytest.mark.parametrize(
    ("kg", "text"), [(0, "0 kg"), (640, "640 kg"), (12500, "12'500 kg"), (12499.6, "12'500 kg")]
)
def test_format_tonnage(kg: float, text: str) -> None:
    assert stats.format_tonnage(kg) == text
