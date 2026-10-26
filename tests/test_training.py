from datetime import UTC, date, datetime

import pytest

from core.models import Workout, WorkoutSet
from core.training import (
    date_from_picker,
    day_label,
    format_date,
    format_set,
    format_set_compact,
    format_weight,
    group_sets_by_exercise,
    month_label,
    parse_reps,
    parse_weight,
    suggest_next_set,
    volume_label,
    workout_title,
)


def make_set(
    set_number: int, reps: int, weight_kg: float | None, exercise_id: int = 1
) -> WorkoutSet:
    return WorkoutSet(
        id=set_number,
        workout_id=1,
        exercise_id=exercise_id,
        set_number=set_number,
        reps=reps,
        weight_kg=weight_kg,
    )


# --- parse_weight ---


@pytest.mark.parametrize(
    ("text", "expected"),
    [("80", 80.0), ("82.5", 82.5), ("82,5", 82.5), (" 60 ", 60.0), ("0", 0.0)],
)
def test_parse_weight(text: str, expected: float) -> None:
    assert parse_weight(text) == expected


@pytest.mark.parametrize("text", ["", "   ", None])
def test_parse_weight_empty_means_bodyweight(text: str | None) -> None:
    assert parse_weight(text) is None


@pytest.mark.parametrize("text", ["abc", "-5", "8o"])
def test_parse_weight_rejects_invalid(text: str) -> None:
    with pytest.raises(ValueError):
        parse_weight(text)


# --- parse_reps ---


def test_parse_reps() -> None:
    assert parse_reps(" 8 ") == 8


@pytest.mark.parametrize("text", ["", None, "0", "-3", "8.5", "acht"])
def test_parse_reps_rejects_invalid(text: str | None) -> None:
    with pytest.raises(ValueError):
        parse_reps(text)


# --- formatting ---


@pytest.mark.parametrize(("weight", "expected"), [(80.0, "80"), (82.5, "82.5"), (1.25, "1.25")])
def test_format_weight(weight: float, expected: str) -> None:
    assert format_weight(weight) == expected


def test_format_set_with_weight() -> None:
    assert format_set(make_set(1, 8, 82.5)) == "82.5 kg × 8"


def test_format_set_bodyweight() -> None:
    assert format_set(make_set(1, 12, None)) == "BW × 12"


def test_format_date() -> None:
    assert format_date(date(2026, 10, 5)) == "05.10.2026"


def test_workout_title_uses_name() -> None:
    assert workout_title(Workout(1, "Chestday", date(2026, 10, 22))) == "Chestday"


def test_workout_title_falls_back_to_date() -> None:
    assert workout_title(Workout(1, "  ", date(2026, 10, 22))) == "Workout 22.10.2026"


# --- group_sets_by_exercise ---


def test_group_sets_by_exercise_keeps_first_appearance_order() -> None:
    sets = [
        make_set(1, 8, 80, exercise_id=2),
        make_set(1, 12, None, exercise_id=5),
        make_set(2, 6, 85, exercise_id=2),
    ]
    groups = group_sets_by_exercise(sets)
    assert [exercise_id for exercise_id, _ in groups] == [2, 5]
    assert [s.set_number for s in groups[0][1]] == [1, 2]


def test_group_sets_by_exercise_empty() -> None:
    assert group_sets_by_exercise([]) == []


# --- suggest_next_set ---


def test_suggest_first_set_from_last_time() -> None:
    last_time = [make_set(1, 8, 80), make_set(2, 6, 85)]
    assert suggest_next_set(last_time, current=[]) == (80, 8)


def test_suggest_matches_set_number_of_last_time() -> None:
    last_time = [make_set(1, 8, 80), make_set(2, 6, 85)]
    current = [make_set(1, 8, 82.5)]
    assert suggest_next_set(last_time, current) == (85, 6)


def test_suggest_repeats_previous_set_when_last_time_had_fewer() -> None:
    last_time = [make_set(1, 8, 80)]
    current = [make_set(1, 8, 82.5), make_set(2, 7, 82.5)]
    assert suggest_next_set(last_time, current) == (82.5, 7)


def test_suggest_without_history_uses_previous_set() -> None:
    assert suggest_next_set([], [make_set(1, 10, None)]) == (None, 10)


def test_suggest_nothing_known() -> None:
    assert suggest_next_set([], []) is None


# --- date_from_picker ---


@pytest.mark.parametrize(
    "value",
    [
        # Local midnight on 22.10. as sent by the phone, normalized to UTC:
        datetime(2026, 10, 21, 22, 0, tzinfo=UTC),  # Zurich summer time (UTC+2)
        datetime(2026, 10, 21, 23, 0, tzinfo=UTC),  # Zurich winter time (UTC+1)
        datetime(2026, 10, 22, 5, 0, tzinfo=UTC),  # New York (UTC-5)
        datetime(2026, 10, 22, 0, 0, tzinfo=UTC),  # UTC
        datetime(2026, 10, 22, 0, 0),  # naive
        date(2026, 10, 22),
    ],
)
def test_date_from_picker_returns_picked_day(value: datetime | date) -> None:
    assert date_from_picker(value) == date(2026, 10, 22)


# --- day_label ---


@pytest.mark.parametrize(
    ("day", "text"),
    [
        (date(2026, 10, 26), "Heute"),
        (date(2026, 10, 25), "Gestern"),
        (date(2026, 10, 20), "Di · 20. Okt"),
        (date(2026, 3, 2), "Mo · 2. Mär"),
        (date(2025, 12, 28), "So · 28. Dez 2025"),  # other year shows the year
    ],
)
def test_day_label(day: date, text: str) -> None:
    assert day_label(day, today=date(2026, 10, 26)) == text


@pytest.mark.parametrize(
    ("exercises", "sets", "text"),
    [(0, 0, "Noch leer"), (1, 1, "1 Übung · 1 Satz"), (2, 5, "2 Übungen · 5 Sätze")],
)
def test_volume_label(exercises: int, sets: int, text: str) -> None:
    assert volume_label(exercises, sets) == text


@pytest.mark.parametrize(
    ("day", "text"), [(date(2026, 10, 3), "Oktober"), (date(2025, 3, 9), "März 2025")]
)
def test_month_label(day: date, text: str) -> None:
    assert month_label(day, today=date(2026, 10, 26)) == text


def test_format_set_compact() -> None:
    assert format_set_compact(make_set(1, 8, 82.5)) == "82.5 × 8"
    assert format_set_compact(make_set(1, 12, None)) == "BW × 12"
