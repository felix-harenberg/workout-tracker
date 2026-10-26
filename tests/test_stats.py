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


# --- PRs ---


def test_exercise_pr_is_heaviest_set(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Bench", (8, 80), (6, 85))
    log(conn, date(2026, 10, 8), "Bench", (6, 90), (3, 95))

    pr = stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Bench").id)

    assert pr is not None
    assert (pr.workout_set.weight_kg, pr.workout_set.reps) == (95, 3)
    assert pr.date == date(2026, 10, 8)


def test_exercise_pr_tie_prefers_more_reps(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Bench", (3, 95))
    log(conn, date(2026, 10, 8), "Bench", (5, 95))
    pr = stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Bench").id)
    assert pr is not None
    assert pr.workout_set.reps == 5
    assert pr.date == date(2026, 10, 8)


def test_exercise_pr_ignores_bodyweight_sets(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Pull-ups", (10, None))
    assert stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Pull-ups").id) is None


def test_exercise_pr_ignores_other_exercises(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Squat", (5, 140))
    log(conn, date(2026, 10, 1), "Bench", (5, 80))
    pr = stats.exercise_pr(conn, repo.get_or_create_exercise(conn, "Bench").id)
    assert pr is not None
    assert pr.workout_set.weight_kg == 80


# --- Max weight history ---


def test_max_weight_history_heaviest_set_per_day(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 8), "Bench", (6, 90), (3, 95))
    log(conn, date(2026, 10, 1), "Bench", (8, 80), (6, 85))
    log(conn, date(2026, 10, 5), "Pull-ups", (10, None))

    history = stats.max_weight_history(conn, repo.get_or_create_exercise(conn, "Bench").id)

    assert history == [(date(2026, 10, 1), 85), (date(2026, 10, 8), 95)]


def test_max_weight_history_two_workouts_same_day_merge(conn: sqlite3.Connection) -> None:
    log(conn, date(2026, 10, 1), "Bench", (5, 80))
    log(conn, date(2026, 10, 1), "Bench", (5, 90))
    history = stats.max_weight_history(conn, repo.get_or_create_exercise(conn, "Bench").id)
    assert history == [(date(2026, 10, 1), 90)]


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


@pytest.mark.parametrize(
    ("kg", "text"), [(0, "0 kg"), (640, "640 kg"), (12500, "12'500 kg"), (12499.6, "12'500 kg")]
)
def test_format_tonnage(kg: float, text: str) -> None:
    assert stats.format_tonnage(kg) == text
