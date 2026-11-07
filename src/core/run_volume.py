"""Running volume: kilometres per run, a goal per week (Monday to Sunday), and what the
running page shows about them. Only distance; pace stays with the watch and Strava."""

import csv
import io
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from core.training import format_weight

FIRST_GOAL_KM = 20.0
GROWTH = 1.1  # suggested goal: last goal + 10 %


@dataclass(frozen=True)
class RunEntry:
    id: int
    date: date
    distance_km: float


@dataclass(frozen=True)
class WeekKm:
    week: date  # its Monday
    km: float
    goal: float | None


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def format_km(km: float) -> str:
    """5 -> "5", 7.5 -> "7.5", 10.25 -> "10.25"."""
    return format_weight(km)


def parse_km(text: str | None) -> float:
    try:
        km = float((text or "").strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"Invalid distance: {text!r}") from None
    if km <= 0:
        raise ValueError("Distance must be positive")
    return km


def step_km(text: str | None, delta: float) -> str:
    """The ±0.5 / ±1 km buttons; never below 0.5. Empty counts as 0, unreadable stays."""
    if not (text or "").strip():
        return format_km(max(delta, 0.5))
    try:
        km = parse_km(text)
    except ValueError:
        return text or ""
    return format_km(max(round(km + delta, 2), 0.5))


# --- Runs ---


def add_run(conn: sqlite3.Connection, day: date, distance_km: float) -> RunEntry:
    _check(distance_km)
    with conn:
        cursor = conn.execute(
            "INSERT INTO run_entry (date, distance_km) VALUES (?, ?)",
            (day.isoformat(), distance_km),
        )
    return RunEntry(cursor.lastrowid, day, distance_km)


def update_run(conn: sqlite3.Connection, run_id: int, day: date, distance_km: float) -> None:
    _check(distance_km)
    with conn:
        conn.execute(
            "UPDATE run_entry SET date = ?, distance_km = ? WHERE id = ?",
            (day.isoformat(), distance_km, run_id),
        )


def delete_run(conn: sqlite3.Connection, run_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM run_entry WHERE id = ?", (run_id,))


def runs_in_week(conn: sqlite3.Connection, week: date) -> list[RunEntry]:
    """The runs of the week that `week` falls in, oldest first."""
    monday = week_start(week)
    rows = conn.execute(
        "SELECT id, date, distance_km FROM run_entry WHERE date BETWEEN ? AND ? ORDER BY date, id",
        (monday.isoformat(), (monday + timedelta(days=6)).isoformat()),
    ).fetchall()
    return [RunEntry(i, date.fromisoformat(d), km) for i, d, km in rows]


def week_km(conn: sqlite3.Connection, week: date) -> float:
    return round(sum(r.distance_km for r in runs_in_week(conn, week)), 2)


def _check(distance_km: float) -> None:
    if distance_km <= 0:
        raise ValueError("Distance must be positive")


# --- Goals ---


def get_goal(conn: sqlite3.Connection, week: date) -> float | None:
    row = conn.execute(
        "SELECT km FROM run_goal WHERE week_start = ?", (week_start(week).isoformat(),)
    ).fetchone()
    return row[0] if row else None


def set_goal(conn: sqlite3.Connection, week: date, km: float) -> None:
    _check(km)
    with conn:
        conn.execute(
            "INSERT INTO run_goal (week_start, km) VALUES (?, ?)"
            " ON CONFLICT(week_start) DO UPDATE SET km = excluded.km",
            (week_start(week).isoformat(), km),
        )


def suggest_goal(conn: sqlite3.Connection, week: date) -> float:
    """The latest goal before this week + 10 %, rounded to half a kilometre; 20 at first."""
    row = conn.execute(
        "SELECT km FROM run_goal WHERE week_start < ? ORDER BY week_start DESC LIMIT 1",
        (week_start(week).isoformat(),),
    ).fetchone()
    if row is None:
        return FIRST_GOAL_KM
    return round(row[0] * GROWTH * 2) / 2


def goal_label(km: float, goal: float | None) -> str:
    if goal is None:
        return "Kein Ziel gesetzt"
    left = round(goal - km, 2)
    if left > 0:
        return f"noch {format_km(left)} km"
    if left == 0:
        return "Ziel erreicht"
    return f"Ziel erreicht · +{format_km(-left)} km"


def history(conn: sqlite3.Connection, today: date, weeks: int = 12) -> list[WeekKm]:
    """Km and goal per week up to this one, oldest first, including weeks without runs.

    Starts at the first week with a run or a goal, but at most `weeks` back.
    """
    first = conn.execute(
        "SELECT MIN(d) FROM (SELECT MIN(date) AS d FROM run_entry"
        " UNION ALL SELECT MIN(week_start) FROM run_goal)"
    ).fetchone()[0]
    if first is None:
        return []
    this_week = week_start(today)
    start = max(week_start(date.fromisoformat(first)), this_week - timedelta(weeks=weeks - 1))
    result = []
    week = start
    while week <= this_week:
        result.append(WeekKm(week, week_km(conn, week), get_goal(conn, week)))
        week += timedelta(weeks=1)
    return result


def export_runs_csv(conn: sqlite3.Connection) -> str:
    """One row per run with the goal of its week."""
    rows = conn.execute(
        "SELECT r.date, r.distance_km FROM run_entry r ORDER BY r.date, r.id"
    ).fetchall()
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["date", "distance_km", "week_goal_km"])
    for iso_date, km in rows:
        goal = get_goal(conn, date.fromisoformat(iso_date))
        writer.writerow([iso_date, format_km(km), format_km(goal) if goal is not None else ""])
    return buffer.getvalue()
