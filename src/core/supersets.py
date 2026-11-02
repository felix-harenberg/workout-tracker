"""Supersets: exercises of a workout done in turns, and which one comes next."""

import sqlite3
from string import ascii_uppercase

from core import repository as repo
from core.models import Superset, Workout


def list_supersets(conn: sqlite3.Connection, workout_id: int) -> list[Superset]:
    """The workout's groups in order: A, B, ..."""
    rows = conn.execute(
        "SELECT group_no, exercise_id FROM workout_superset WHERE workout_id = ?"
        " ORDER BY group_no, position",
        (workout_id,),
    ).fetchall()
    groups: dict[int, list[int]] = {}
    for group_no, exercise_id in rows:
        groups.setdefault(group_no, []).append(exercise_id)
    info = {
        group_no: (name, notes)
        for group_no, name, notes in conn.execute(
            "SELECT group_no, name, notes FROM workout_superset_info WHERE workout_id = ?",
            (workout_id,),
        )
    }
    return [
        Superset(ascii_uppercase[no], tuple(ids), *info.get(no, ("", "")))
        for no, ids in groups.items()
    ]


def set_info(conn: sqlite3.Connection, workout_id: int, letter: str, name: str, notes: str) -> None:
    """Name and notes of a group, e.g. "Arme" and "ohne Pause zwischen den Übungen"."""
    with conn:
        conn.execute(
            "INSERT INTO workout_superset_info (workout_id, group_no, name, notes)"
            " VALUES (?, ?, ?, ?) ON CONFLICT (workout_id, group_no)"
            " DO UPDATE SET name = excluded.name, notes = excluded.notes",
            (workout_id, ascii_uppercase.index(letter), name.strip(), notes.strip()),
        )


def superset_of(conn: sqlite3.Connection, workout_id: int, exercise_id: int) -> Superset | None:
    return next(
        (s for s in list_supersets(conn, workout_id) if exercise_id in s.exercise_ids), None
    )


def link(conn: sqlite3.Connection, workout_id: int, exercise_ids: list[int]) -> None:
    """Make a new group of these exercises, in this order (the order they were tapped).

    Exercises that were in another group leave it; a group left with one exercise is gone.
    """
    if len(exercise_ids) < 2 or len(set(exercise_ids)) != len(exercise_ids):
        raise ValueError("A superset needs at least two different exercises")
    with conn:
        conn.executemany(
            "DELETE FROM workout_superset WHERE workout_id = ? AND exercise_id = ?",
            [(workout_id, e) for e in exercise_ids],
        )
        group_no = conn.execute(
            "SELECT COALESCE(MAX(group_no) + 1, 0) FROM workout_superset WHERE workout_id = ?",
            (workout_id,),
        ).fetchone()[0]
        conn.executemany(
            "INSERT INTO workout_superset (workout_id, exercise_id, group_no, position)"
            " VALUES (?, ?, ?, ?)",
            [(workout_id, e, group_no, i) for i, e in enumerate(exercise_ids)],
        )
        _tidy(conn, workout_id)


def unlink(conn: sqlite3.Connection, workout_id: int, letter: str) -> None:
    """Split a group; its exercises stay in the workout, just no longer in turns."""
    with conn:
        conn.execute(
            "DELETE FROM workout_superset WHERE workout_id = ? AND group_no = ?",
            (workout_id, ascii_uppercase.index(letter)),
        )
        _tidy(conn, workout_id)


def remove_exercise(conn: sqlite3.Connection, workout_id: int, exercise_id: int) -> None:
    """Take an exercise out of its group, e.g. when it is removed from the workout."""
    with conn:
        conn.execute(
            "DELETE FROM workout_superset WHERE workout_id = ? AND exercise_id = ?",
            (workout_id, exercise_id),
        )
        _tidy(conn, workout_id)


def copy_groups(conn: sqlite3.Connection, source_id: int, target_id: int) -> None:
    for superset in list_supersets(conn, source_id):
        link(conn, target_id, list(superset.exercise_ids))
        if superset.name or superset.notes:
            letter = list_supersets(conn, target_id)[-1].letter  # a new group comes last
            set_info(conn, target_id, letter, superset.name, superset.notes)


def _tidy(conn: sqlite3.Connection, workout_id: int) -> None:
    """Drop groups of one, then number groups and positions 0, 1, 2 ... without gaps,
    so the letters stay A, B, C even after a group in the middle is gone. Name and notes
    go with their group, or away with it."""
    conn.execute(
        "DELETE FROM workout_superset WHERE workout_id = :w AND group_no IN"
        " (SELECT group_no FROM workout_superset WHERE workout_id = :w"
        "  GROUP BY group_no HAVING COUNT(*) < 2)",
        {"w": workout_id},
    )
    rows = conn.execute(
        "SELECT exercise_id, group_no FROM workout_superset WHERE workout_id = ?"
        " ORDER BY group_no, position",
        (workout_id,),
    ).fetchall()
    numbers = {old: new for new, old in enumerate(dict.fromkeys(g for _, g in rows))}
    conn.execute(
        "DELETE FROM workout_superset_info WHERE workout_id = ? AND group_no NOT IN"
        f" ({', '.join('?' * len(numbers))})",
        (workout_id, *numbers),
    )
    # Ascending, every group moves down into a number that is free by then.
    for old, new in numbers.items():
        conn.execute(
            "UPDATE workout_superset_info SET group_no = ? WHERE workout_id = ? AND group_no = ?",
            (new, workout_id, old),
        )
    position: dict[int, int] = {}
    for exercise_id, group_no in rows:
        new = numbers[group_no]
        conn.execute(
            "UPDATE workout_superset SET group_no = ?, position = ?"
            " WHERE workout_id = ? AND exercise_id = ?",
            (new, position.get(new, 0), workout_id, exercise_id),
        )
        position[new] = position.get(new, 0) + 1


def next_member(
    order: list[int], current: int, done: dict[int, int], targets: dict[int, int | None]
) -> int | None:
    """The exercise after `current` in the group, going round.

    An exercise is finished when it has as many sets as last time (`targets`); finished
    ones are skipped. Without a last time (target None) an exercise is never finished.
    If only `current` is left, it is the next one; if all are finished, None.
    """
    start = order.index(current)
    for step in range(1, len(order) + 1):
        candidate = order[(start + step) % len(order)]
        target = targets.get(candidate)
        if target is None or done.get(candidate, 0) < target:
            return candidate
    return None


def next_in_superset(conn: sqlite3.Connection, workout: Workout, exercise_id: int) -> int | None:
    """Where to go after a set of `exercise_id` was saved; None if it is in no superset
    or the superset is done."""
    superset = superset_of(conn, workout.id, exercise_id)
    if superset is None:
        return None
    done: dict[int, int] = {}
    for s in repo.list_sets(conn, workout.id):
        done[s.exercise_id] = done.get(s.exercise_id, 0) + 1
    targets: dict[int, int | None] = {}
    for member in superset.exercise_ids:
        last = repo.last_sets_for_exercise(conn, member, before=workout)
        targets[member] = len(last[1]) if last else None
    return next_member(list(superset.exercise_ids), exercise_id, done, targets)
