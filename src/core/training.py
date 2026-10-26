"""Input parsing, formatting and suggestions for logging strength training."""

from datetime import date, datetime, timedelta

from core.models import Hint, WeightHint, Workout, WorkoutSet


def parse_weight(text: str | None) -> float | None:
    """Parse a weight in kg. Accepts "82.5" and "82,5". Empty means bodyweight (None)."""
    text = (text or "").strip()
    if not text:
        return None
    weight = float(text.replace(",", "."))
    if weight < 0:
        raise ValueError("Weight must not be negative")
    return weight


def parse_reps(text: str | None) -> int:
    reps = int((text or "").strip())
    if reps <= 0:
        raise ValueError("Reps must be positive")
    return reps


def format_weight(weight_kg: float) -> str:
    """80.0 -> "80", 82.5 -> "82.5"."""
    return f"{weight_kg:g}"


def format_weight_reps(weight_kg: float | None, reps: int) -> str:
    """Weight and reps as text: "85 kg × 6", or "BW × 12" for bodyweight."""
    if weight_kg is None:
        return f"BW × {reps}"
    return f"{format_weight(weight_kg)} kg × {reps}"


def format_set(workout_set: WorkoutSet) -> str:
    return format_weight_reps(workout_set.weight_kg, workout_set.reps)


def format_set_compact(workout_set: WorkoutSet) -> str:
    """Without the unit, for chips: "82.5 × 8", "BW × 12"."""
    if workout_set.weight_kg is None:
        return f"BW × {workout_set.reps}"
    return f"{format_weight(workout_set.weight_kg)} × {workout_set.reps}"


def format_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def date_from_picker(value: datetime | date) -> date:
    """The day picked in a date picker.

    The phone sends local midnight converted to UTC (e.g. 22.10. 00:00 in Zurich
    arrives as 21.10. 22:00 UTC). Rounding to the nearest day recovers the picked
    day without knowing the phone's time zone.
    """
    if not isinstance(value, datetime):
        return value
    return (value + timedelta(hours=12)).date()


def workout_title(workout: Workout) -> str:
    return workout.name.strip() or f"Workout {format_date(workout.date)}"


def group_sets_by_exercise(sets: list[WorkoutSet]) -> list[tuple[int, list[WorkoutSet]]]:
    """Group sets by exercise id, ordered by when each exercise was first logged."""
    groups: dict[int, list[WorkoutSet]] = {}
    for workout_set in sets:
        groups.setdefault(workout_set.exercise_id, []).append(workout_set)
    return list(groups.items())


def suggest_next_set(
    last_time: list[WorkoutSet], current: list[WorkoutSet]
) -> tuple[float | None, int] | None:
    """Suggest (weight_kg, reps) for the next set of one exercise.

    Uses the set with the same number from last time; if last time had fewer sets,
    repeats the previous set from today. Returns None if nothing is known.
    """
    index = len(current)
    if index < len(last_time):
        reference = last_time[index]
    elif current:
        reference = current[-1]
    else:
        return None
    return reference.weight_kg, reference.reps


_WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def day_label(day: date, today: date) -> str:
    """Short German day label: "Heute", "Gestern" or e.g. "Di · 20. Okt" (year if not this year)."""
    if day == today:
        return "Heute"
    if day == today - timedelta(days=1):
        return "Gestern"
    label = f"{_WEEKDAYS[day.weekday()]} · {day.day}. {_MONTHS[day.month - 1]}"
    return label if day.year == today.year else f"{label} {day.year}"


def volume_label(exercises: int, sets: int) -> str:
    """Size of a workout, e.g. "2 Übungen · 5 Sätze"; "Noch leer" without sets."""
    if sets == 0:
        return "Noch leer"
    exercise_word = "Übung" if exercises == 1 else "Übungen"
    set_word = "Satz" if sets == 1 else "Sätze"
    return f"{exercises} {exercise_word} · {sets} {set_word}"


_MONTH_NAMES = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]  # fmt: skip


def month_label(day: date, today: date) -> str:
    """Month heading for a list, e.g. "Oktober" or "März 2025" (year if not this year)."""
    name = _MONTH_NAMES[day.month - 1]
    return name if day.year == today.year else f"{name} {day.year}"


def hint_message(hint: WeightHint, today: date) -> str:
    """The next-time reminder as a sentence, e.g. "Mehr Gewicht hast du dir gestern vorgenommen"."""
    amount = "Mehr" if hint.direction == Hint.UP else "Weniger"
    when = ""
    if hint.set_on:
        day = day_label(hint.set_on, today)
        when = f" {day.lower()}" if day in ("Heute", "Gestern") else f" am {day}"
    return f"{amount} Gewicht hast du dir{when} vorgenommen"
