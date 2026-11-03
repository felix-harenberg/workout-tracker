import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from core import repository as repo
from core import supersets as ss
from core.db import MIGRATIONS, connect
from core.export import export_csv
from core.models import Superset
from core.templates import copy_supersets_from_last


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


def exercises(conn: sqlite3.Connection, *names: str) -> list[int]:
    return [repo.get_or_create_exercise(conn, name).id for name in names]


# --- Linking ---


def test_no_supersets_by_default(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    assert ss.list_supersets(conn, workout.id) == []


def test_link_keeps_the_tapped_order(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    curls, triceps, raises = exercises(conn, "Curls", "Trizeps", "Seitheben")

    ss.link(conn, workout.id, [triceps, curls, raises])

    assert ss.list_supersets(conn, workout.id) == [Superset("A", (triceps, curls, raises))]


def test_label_per_exercise(conn: sqlite3.Connection) -> None:
    superset = Superset("B", (5, 3))
    assert superset.label(5) == "B1"
    assert superset.label(3) == "B2"


def test_several_groups_get_letters_in_order(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c, d = exercises(conn, "Curls", "Trizeps", "Bench", "Rows")

    ss.link(conn, workout.id, [a, b])
    ss.link(conn, workout.id, [c, d])

    assert ss.list_supersets(conn, workout.id) == [Superset("A", (a, b)), Superset("B", (c, d))]
    assert ss.superset_of(conn, workout.id, d) == Superset("B", (c, d))
    assert ss.superset_of(conn, workout.id, exercises(conn, "Dips")[0]) is None


def test_linking_moves_exercises_out_of_their_old_group(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c = exercises(conn, "Curls", "Trizeps", "Seitheben")
    ss.link(conn, workout.id, [a, b])

    ss.link(conn, workout.id, [b, c])

    # A would be alone, so its group is gone; the new group becomes A.
    assert ss.list_supersets(conn, workout.id) == [Superset("A", (b, c))]


def test_link_needs_two_different_exercises(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    (a,) = exercises(conn, "Curls")
    with pytest.raises(ValueError):
        ss.link(conn, workout.id, [a])
    with pytest.raises(ValueError):
        ss.link(conn, workout.id, [a, a])


def test_unlink_renames_the_later_groups(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c, d = exercises(conn, "Curls", "Trizeps", "Bench", "Rows")
    ss.link(conn, workout.id, [a, b])
    ss.link(conn, workout.id, [c, d])

    ss.unlink(conn, workout.id, "A")

    assert ss.list_supersets(conn, workout.id) == [Superset("A", (c, d))]


def test_removing_an_exercise_closes_the_gap(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c = exercises(conn, "Curls", "Trizeps", "Seitheben")
    ss.link(conn, workout.id, [a, b, c])

    ss.remove_exercise(conn, workout.id, b)
    assert ss.list_supersets(conn, workout.id) == [Superset("A", (a, c))]

    ss.remove_exercise(conn, workout.id, a)
    assert ss.list_supersets(conn, workout.id) == []  # one exercise alone is no superset


def test_groups_belong_to_the_workout(conn: sqlite3.Connection) -> None:
    monday = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    thursday = repo.create_workout(conn, "Arms", date(2026, 11, 5))
    a, b = exercises(conn, "Curls", "Trizeps")
    ss.link(conn, monday.id, [a, b])

    assert ss.list_supersets(conn, thursday.id) == []

    repo.delete_workout(conn, monday.id)
    assert ss.list_supersets(conn, monday.id) == []


# --- Next exercise ---


@pytest.mark.parametrize(
    ("current", "done", "targets", "expected"),
    [
        # Round robin: A1 → A2 → A3 → A1
        (1, {1: 1}, {1: 3, 2: 3, 3: 3}, 2),
        (3, {1: 1, 2: 1, 3: 1}, {1: 3, 2: 3, 3: 3}, 1),
        # A2 has all of last time's sets: skipped
        (1, {1: 3, 2: 2, 3: 2}, {1: 3, 2: 2, 3: 3}, 3),
        # Everybody else is done: stay on the current one
        (1, {1: 3, 2: 2}, {1: 4, 2: 2}, 1),
        # All done, e.g. last time's sets were taken over: still alternate
        (2, {1: 3, 2: 3}, {1: 3, 2: 3}, 1),
        (1, {1: 4, 2: 3, 3: 3}, {1: 3, 2: 3, 3: 3}, 2),
        # First time (no target): never done, keep going round
        (2, {1: 5, 2: 5}, {1: None, 2: None}, 1),
    ],
)
def test_next_member(
    current: int, done: dict[int, int], targets: dict[int, int | None], expected: int
) -> None:
    assert ss.next_member([1, 2, 3][: len(targets)], current, done, targets) == expected


def test_next_in_superset_uses_last_time(conn: sqlite3.Connection) -> None:
    curls, triceps = exercises(conn, "Curls", "Trizeps")
    last = repo.create_workout(conn, "Arms", date(2026, 10, 30))
    for _ in range(3):
        repo.add_set(conn, last.id, curls, reps=10, weight_kg=12)
    repo.add_set(conn, last.id, triceps, reps=12, weight_kg=20)
    today = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    ss.link(conn, today.id, [curls, triceps])

    repo.add_set(conn, today.id, curls, reps=10, weight_kg=12)
    assert ss.next_in_superset(conn, today, curls) == triceps

    repo.add_set(conn, today.id, triceps, reps=12, weight_kg=20)
    assert ss.next_in_superset(conn, today, triceps) == curls  # Trizeps is done

    assert ss.next_in_superset(conn, today, exercises(conn, "Dips")[0]) is None


# --- Repeating a workout ---


def test_new_workout_takes_the_groups_from_last_time(conn: sqlite3.Connection) -> None:
    a, b, c = exercises(conn, "Curls", "Trizeps", "Seitheben")
    last = repo.create_workout(conn, "Arms", date(2026, 10, 30))
    repo.add_set(conn, last.id, a, reps=10, weight_kg=12)
    ss.link(conn, last.id, [a, b, c])
    other = repo.create_workout(conn, "Legs", date(2026, 11, 1))
    repo.add_set(conn, other.id, a, reps=10, weight_kg=12)
    ss.link(conn, other.id, [a, b])

    today = repo.create_workout(conn, " arms ", date(2026, 11, 2))
    copy_supersets_from_last(conn, today)

    assert ss.list_supersets(conn, today.id) == [Superset("A", (a, b, c))]


def test_copy_keeps_groups_that_are_already_there(conn: sqlite3.Connection) -> None:
    a, b, c = exercises(conn, "Curls", "Trizeps", "Seitheben")
    last = repo.create_workout(conn, "Arms", date(2026, 10, 30))
    repo.add_set(conn, last.id, a, reps=10, weight_kg=12)
    ss.link(conn, last.id, [a, b])
    today = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    ss.link(conn, today.id, [b, c])

    copy_supersets_from_last(conn, today)

    assert ss.list_supersets(conn, today.id) == [Superset("A", (b, c))]


# --- Export and migration ---


def test_superset_letter_in_csv_export(conn: sqlite3.Connection) -> None:
    a, b, c = exercises(conn, "Curls", "Trizeps", "Bench")
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    for exercise_id in (a, b, c):
        repo.add_set(conn, workout.id, exercise_id, reps=10, weight_kg=20)
    ss.link(conn, workout.id, [a, b])

    header, *rows = export_csv(conn).splitlines()
    column = header.split(",").index("superset")
    assert [row.split(",")[column] for row in rows] == ["A", "A", ""]


def test_v5_database_gets_superset_table(tmp_path: Path) -> None:
    db_path = tmp_path / "v5.db"
    old = sqlite3.connect(db_path)
    for script in MIGRATIONS[:5]:
        old.executescript(script)
    old.executescript(
        "INSERT INTO workout (id, name, date) VALUES (1, 'Arms', '2026-11-02');"
        " PRAGMA user_version = 5;"
    )
    old.close()

    conn = connect(db_path)
    assert ss.list_supersets(conn, 1) == []
    conn.close()


# --- Name and notes ---


def test_title_with_and_without_name() -> None:
    assert Superset("A", (1, 2)).title == "Superset A"
    assert Superset("B", (1, 2), name="Arme").title == "B · Arme"


def test_name_and_notes_are_saved_per_group(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c, d = exercises(conn, "Curls", "Trizeps", "Bench", "Rows")
    ss.link(conn, workout.id, [a, b])
    ss.link(conn, workout.id, [c, d])

    ss.set_info(conn, workout.id, "B", "  Push Pull ", " ohne Pause\n")

    first, second = ss.list_supersets(conn, workout.id)
    assert (first.name, first.notes) == ("", "")
    assert (second.name, second.notes) == ("Push Pull", "ohne Pause")


def test_splitting_deletes_name_and_notes(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c, d = exercises(conn, "Curls", "Trizeps", "Bench", "Rows")
    ss.link(conn, workout.id, [a, b])
    ss.set_info(conn, workout.id, "A", "Arme", "90 s Pause nach der Runde")

    ss.unlink(conn, workout.id, "A")
    ss.link(conn, workout.id, [c, d])  # gets letter A again, but not the old name

    assert ss.list_supersets(conn, workout.id) == [Superset("A", (c, d))]


def test_name_moves_with_its_group_when_letters_change(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c, d = exercises(conn, "Curls", "Trizeps", "Bench", "Rows")
    ss.link(conn, workout.id, [a, b])
    ss.link(conn, workout.id, [c, d])
    ss.set_info(conn, workout.id, "B", "Push Pull", "")

    ss.remove_exercise(conn, workout.id, a)  # A is gone, B becomes A

    assert ss.list_supersets(conn, workout.id) == [Superset("A", (c, d), name="Push Pull")]


def test_group_of_one_left_loses_its_name(conn: sqlite3.Connection) -> None:
    workout = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    a, b, c = exercises(conn, "Curls", "Trizeps", "Bench")
    ss.link(conn, workout.id, [a, b])
    ss.set_info(conn, workout.id, "A", "Arme", "")

    ss.remove_exercise(conn, workout.id, a)
    ss.link(conn, workout.id, [b, c])

    assert ss.list_supersets(conn, workout.id) == [Superset("A", (b, c))]


def test_new_workout_takes_name_and_notes_along(conn: sqlite3.Connection) -> None:
    a, b = exercises(conn, "Curls", "Trizeps")
    last = repo.create_workout(conn, "Arms", date(2026, 10, 30))
    repo.add_set(conn, last.id, a, reps=10, weight_kg=12)
    ss.link(conn, last.id, [a, b])
    ss.set_info(conn, last.id, "A", "Arme", "ohne Pause")

    today = repo.create_workout(conn, "Arms", date(2026, 11, 2))
    copy_supersets_from_last(conn, today)

    assert ss.list_supersets(conn, today.id) == [
        Superset("A", (a, b), name="Arme", notes="ohne Pause")
    ]
