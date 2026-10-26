"""Record moments: notice a new heaviest set, and ask first if the jump looks like a typo."""

import random
import sqlite3
from dataclasses import dataclass
from datetime import date

from core import stats
from core.models import WorkoutSet

SUSPICIOUS_JUMP = 1.2  # more than 20 % above the previous best

QUOTES = [
    "Was hast du anderes erwartet?",
    "Überrascht? Wir nicht.",
    "So sieht Durchziehen aus.",
    "Nicht Glück. Training.",
    "Letzte Woche war gestern.",
    "Die Stange hat's auch gemerkt.",
]


@dataclass(frozen=True)
class RecordCheck:
    is_record: bool  # heavier than any set of this exercise so far
    suspicious: bool  # so much heavier that it may be a typo
    previous_best: WorkoutSet | None
    previous_date: date | None


def check_new_set(
    conn: sqlite3.Connection, exercise_id: int, weight_kg: float | None
) -> RecordCheck:
    """Check a set before it is saved. The first weighted set of an exercise is no record."""
    pr = stats.exercise_pr(conn, exercise_id)
    if pr is None or weight_kg is None:
        return RecordCheck(False, False, pr.workout_set if pr else None, pr.date if pr else None)

    best = pr.workout_set.weight_kg
    # Rounded, so that exactly 20 % (82.5 -> 99) is not flagged because of float noise.
    ratio = round(weight_kg / best, 6) if best else float("inf")
    return RecordCheck(
        is_record=weight_kg > best,
        suspicious=ratio > SUSPICIOUS_JUMP,
        previous_best=pr.workout_set,
        previous_date=pr.date,
    )


def suspicious_message(weight_kg: float, previous_kg: float) -> str:
    """E.g. "Zehnmal so viel wie dein Bestwert. Vertippt, oder bist du jetzt einfach so?"."""
    ratio = weight_kg / previous_kg
    if ratio >= 1.95:
        times = round(ratio)
        amount = {2: "Doppelt", 10: "Zehnmal"}.get(times, f"{times}-mal")
        comparison = f"{amount} so viel wie dein Bestwert"
    else:
        comparison = f"{round((ratio - 1) * 100)} % mehr als dein Bestwert"
    return f"{comparison}. Vertippt, oder bist du jetzt einfach so?"


def pick_quote(rng: random.Random | None = None) -> str:
    return (rng or random).choice(QUOTES)
