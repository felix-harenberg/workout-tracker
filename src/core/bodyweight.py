"""Bodyweight: one entry per day, a goal weight, and what the weight page shows about it."""

import calendar
import csv
import io
import sqlite3
from datetime import date

from core.training import format_weight, parse_weight

GOAL_KEY = "bodyweight_goal_kg"
PERIODS = ["1M", "3M", "1J", "Alles"]
_PERIOD_MONTHS = {"1M": 1, "3M": 3, "1J": 12}


def log_weight(conn: sqlite3.Connection, day: date, weight_kg: float) -> None:
    """Save the weight of a day; a second entry on the same day replaces the first."""
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    with conn:
        conn.execute(
            "INSERT INTO bodyweight (date, weight_kg) VALUES (?, ?)"
            " ON CONFLICT(date) DO UPDATE SET weight_kg = excluded.weight_kg",
            (day.isoformat(), weight_kg),
        )


def delete_weight(conn: sqlite3.Connection, day: date) -> None:
    with conn:
        conn.execute("DELETE FROM bodyweight WHERE date = ?", (day.isoformat(),))


def list_weights(conn: sqlite3.Connection, since: date | None = None) -> list[tuple[date, float]]:
    """All entries, oldest first; only from `since` on if given."""
    rows = conn.execute(
        "SELECT date, weight_kg FROM bodyweight WHERE date >= ? ORDER BY date",
        ((since or date.min).isoformat(),),
    ).fetchall()
    return [(date.fromisoformat(d), kg) for d, kg in rows]


def latest_weight(conn: sqlite3.Connection) -> tuple[date, float] | None:
    row = conn.execute(
        "SELECT date, weight_kg FROM bodyweight ORDER BY date DESC LIMIT 1"
    ).fetchone()
    return (date.fromisoformat(row[0]), row[1]) if row else None


def get_goal(conn: sqlite3.Connection) -> float | None:
    row = conn.execute("SELECT value FROM setting WHERE key = ?", (GOAL_KEY,)).fetchone()
    return float(row[0]) if row else None


def set_goal(conn: sqlite3.Connection, weight_kg: float | None) -> None:
    """Set the goal weight; None removes it."""
    with conn:
        if weight_kg is None:
            conn.execute("DELETE FROM setting WHERE key = ?", (GOAL_KEY,))
        else:
            conn.execute(
                "INSERT INTO setting (key, value) VALUES (?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (GOAL_KEY, str(weight_kg)),
            )


def goal_label(current_kg: float, goal_kg: float | None) -> str:
    """Distance to the goal, whether losing or gaining: "noch 3.4 kg bis Ziel"."""
    if goal_kg is None:
        return "Kein Ziel gesetzt"
    distance = round(abs(current_kg - goal_kg), 1)
    if distance < 0.1:
        return "Ziel erreicht"
    return f"noch {format_weight(distance)} kg bis Ziel"


def period_start(period: str, today: date) -> date | None:
    """First day shown for "1M", "3M", "1J"; None for "Alles"."""
    months = _PERIOD_MONTHS.get(period)
    if months is None:
        return None
    month_index = today.year * 12 + (today.month - 1) - months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(today.day, calendar.monthrange(year, month)[1])  # 31 Mar -> 28 Feb
    return date(year, month, day)


def step_bodyweight(text: str | None, delta: float) -> str:
    """The ±0.1 / ±0.5 kg buttons, rounded to one decimal. Unreadable input stays."""
    try:
        weight = parse_weight(text)
    except ValueError:
        return text or ""
    if weight is None:
        return text or ""
    return format_weight(max(round(weight + delta, 1), 0))


def export_bodyweight_csv(conn: sqlite3.Connection) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["date", "weight_kg"])
    for day, kg in list_weights(conn):
        writer.writerow([day.isoformat(), format_weight(kg)])
    return buffer.getvalue()
