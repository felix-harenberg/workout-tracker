from datetime import date

import flet as ft

from core import repository as repo
from core import stats, supersets
from core.models import Superset, Workout, WorkoutSet, WorkoutType
from core.run import format_distance, format_duration, format_pace, pace_s_per_km
from core.templates import copy_pending_exercises, pending_exercises
from core.training import (
    day_label,
    format_set_compact,
    group_sets_by_exercise,
    volume_label,
    workout_title,
)
from ui import theme
from ui.app import App


def workout_detail_view(app: App, workout: Workout) -> ft.View:
    route = f"/workout/{workout.id}"
    is_run = workout.type == WorkoutType.RUN

    controls: list[ft.Control] = [
        theme.title_headline(workout_title(workout), overline=day_label(workout.date, date.today()))
    ]
    if workout.notes:
        controls.append(theme.muted(workout.notes))
    controls += _run_controls(app, workout) if is_run else _strength_controls(app, workout)

    def delete(_: ft.Event) -> None:
        app.page.pop_dialog()
        repo.delete_workout(app.conn, workout.id)
        app.go("/")

    what = "wird" if is_run else "und alle Sätze werden"
    body: list[ft.Control] = [
        theme.name_sentence(
            workout_title(workout),
            f" {what} gelöscht. Das lässt sich nicht rückgängig machen.",
        )
    ]
    if not is_run:
        exercises, sets = repo.workout_volume(app.conn, workout.id)
        if sets:
            body.append(theme.chips(volume_label(exercises, sets).split(" · ")))
    confirm_delete = theme.dialog(
        "Löschen",
        "Workout löschen?",
        body,
        [
            ft.Row(
                [
                    theme.dialog_button("Abbrechen", lambda _: app.page.pop_dialog()),
                    theme.dialog_button("Löschen", delete, "danger"),
                ],
                spacing=10,
            )
        ],
        danger=True,
    )

    return theme.view(
        route,
        controls,
        bar=theme.top_bar(
            app.back,
            [
                theme.icon_button(
                    ft.Icons.EDIT_OUTLINED, lambda _: app.go(f"{route}/edit"), "Bearbeiten"
                ),
                theme.icon_button(
                    ft.Icons.DELETE_OUTLINE,
                    lambda _: app.page.show_dialog(confirm_delete),
                    "Löschen",
                ),
            ],
        ),
        scroll=ft.ScrollMode.AUTO,
        fab=None if is_run else _fab(app, workout),
    )


def _picked(app: App, workout: Workout) -> list[int] | None:
    """Exercises tapped so far while linking a superset in this workout, else None."""
    if app.superset_pick and app.superset_pick[0] == workout.id:
        return app.superset_pick[1]
    return None


def _fab(app: App, workout: Workout) -> ft.Control | None:
    pick = _picked(app, workout)
    if pick is None:
        return theme.fab(
            lambda _: app.go(f"/workout/{workout.id}/add-exercise"), "Übung hinzufügen", "Übung"
        )
    if len(pick) < 2:
        return None

    def connect(_: ft.Event) -> None:
        supersets.link(app.conn, workout.id, pick)
        app.superset_pick = None
        app.render()

    return theme.fab(connect, "Als Superset verbinden", "Verbinden", glyph="⇄")


def _strength_controls(app: App, workout: Workout) -> list[ft.Control]:
    route = f"/workout/{workout.id}"
    logged = group_sets_by_exercise(repo.list_sets(app.conn, workout.id))
    # Only today's workout offers last time's exercises; old ones show what was done.
    pending = pending_exercises(app.conn, workout) if workout.date == date.today() else []
    if not logged and not pending:
        return [theme.muted("Noch keine Übungen. Tippe auf +, um eine hinzuzufügen.")]

    group_of = {
        e: g for g in supersets.list_supersets(app.conn, workout.id) for e in g.exercise_ids
    }
    pick = _picked(app, workout)

    def tap(exercise_id: int) -> None:
        if pick is None:
            app.go(f"{route}/exercise/{exercise_id}")
            return
        if exercise_id in pick:
            pick.remove(exercise_id)
        else:
            pick.append(exercise_id)
        app.render()

    def long_press(exercise_id: int) -> None:
        """On a superset: show it (and offer to split it); otherwise start linking."""
        if pick is not None:
            return
        group = group_of.get(exercise_id)
        if group:
            app.page.show_dialog(_superset_dialog(app, workout, group))
        else:
            app.superset_pick = (workout.id, [exercise_id])
            app.render()

    def card(exercise_id: int, content: ft.Control, is_pending: bool) -> ft.Control:
        group = group_of.get(exercise_id)
        parts: list[ft.Control] = [ft.Container(content, expand=True)]
        if group:
            parts.insert(
                0, ft.Container(theme.label(group.label(exercise_id), theme.BLUE), width=30)
            )
        if pick is not None:
            parts.append(_pick_marker(pick.index(exercise_id) + 1 if exercise_id in pick else None))
        elif is_pending:
            parts.append(ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=theme.BLUE, size=32))
        block = theme.section(ft.Row(parts), on_click=lambda _: tap(exercise_id))
        block.on_long_press = lambda _: long_press(exercise_id)
        return ft.Container(block, opacity=0.7) if is_pending else block  # pending: not done yet

    cards: dict[int, ft.Control] = {}
    for exercise_id, sets in logged:
        exercise = repo.get_exercise(app.conn, exercise_id)
        assert exercise is not None
        cards[exercise_id] = card(
            exercise_id,
            ft.Column(
                [
                    theme.card_name(exercise.name),
                    theme.chips(
                        [format_set_compact(s) for s in sets],
                        highlighted=_pr_index(app, exercise_id, sets),
                    ),
                ],
                spacing=10,
            ),
            is_pending=False,
        )
    for p in pending:
        cards[p.exercise.id] = card(
            p.exercise.id,
            ft.Column(
                [
                    theme.card_name(p.exercise.name),
                    theme.muted("  ·  ".join(format_set_compact(s) for s in p.last_sets)),
                ],
                spacing=4,
            ),
            is_pending=True,
        )

    placed: set[int] = set()

    def place(exercise_id: int) -> list[ft.Control]:
        """The exercise's card, or its whole superset where its first exercise shows up."""
        if exercise_id in placed:
            return []
        group = group_of.get(exercise_id)
        members = [e for e in group.exercise_ids if e in cards] if group else [exercise_id]
        placed.update(members)
        if len(members) < 2:
            return [cards[e] for e in members]
        return [
            ft.Container(
                ft.Column([cards[e] for e in members], spacing=0),
                border=ft.Border(left=ft.BorderSide(2, theme.BLUE)),
                padding=ft.Padding(12, 0, 0, 0),
            )
        ]

    controls: list[ft.Control] = [_pick_header(app, len(pick))] if pick is not None else []
    for exercise_id, _ in logged:
        controls += place(exercise_id)

    pending_cards = [c for p in pending for c in place(p.exercise.id)]
    if pending_cards:

        def take_all(_: ft.Event) -> None:
            copy_pending_exercises(app.conn, workout)
            app.render()

        controls.append(
            ft.Container(
                ft.Row(
                    [
                        theme.label("Vom letzten Mal"),
                        theme.secondary_button("Alles übernehmen", take_all, ft.Icons.DONE_ALL),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding(4, 12, 0, 0),
            )
        )
        controls += pending_cards
    return controls


def _pick_header(app: App, count: int) -> ft.Control:
    def cancel(_: ft.Event) -> None:
        app.superset_pick = None
        app.render()

    return theme.section(
        ft.Column(
            [
                ft.Row(
                    [
                        theme.label("Superset verbinden", theme.BLUE),
                        theme.secondary_button("Abbrechen", cancel),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                theme.muted(
                    "Tippe die Übungen in der Reihenfolge an, in der du sie machst."
                    if count < 2
                    else f"{count} Übungen gewählt."
                ),
            ],
            spacing=8,
        ),
        highlight=True,
    )


def _pick_marker(number: int | None) -> ft.Control:
    """Square on the right while linking: empty, or blue with the order it was tapped in."""
    return ft.Container(
        ft.Text(
            str(number) if number else "",
            size=15,
            color=theme.TEXT,
            style=ft.TextStyle(font_family=theme.MONO_MEDIUM_FONT),
        ),
        width=30,
        height=30,
        alignment=ft.Alignment.CENTER,
        bgcolor=theme.BLUE if number else None,
        border=ft.Border.all(1, theme.BLUE if number else theme.LINE),
    )


def _superset_dialog(app: App, workout: Workout, group: Superset) -> ft.AlertDialog:
    names = []
    for exercise_id in group.exercise_ids:
        exercise = repo.get_exercise(app.conn, exercise_id)
        assert exercise is not None
        names.append(f"{group.label(exercise_id)} {exercise.name}")

    def split(_: ft.Event) -> None:
        supersets.unlink(app.conn, workout.id, group.letter)
        app.page.pop_dialog()
        app.render()

    return theme.dialog(
        f"Superset {group.letter}",
        "Superset",
        [
            theme.muted("Im Wechsel: nach jedem Satz kommt die nächste Übung."),
            theme.chips(names),
        ],
        [
            ft.Row(
                [
                    theme.dialog_button("Schliessen", lambda _: app.page.pop_dialog()),
                    theme.dialog_button("Trennen", split, "main"),
                ],
                spacing=10,
            )
        ],
    )


def _run_controls(app: App, workout: Workout) -> list[ft.Control]:
    run = repo.get_run(app.conn, workout.id)
    assert run is not None
    rows = [
        ("Distanz", format_distance(run.distance_km)),
        ("Dauer", format_duration(run.duration_s)),
        ("Pace", format_pace(pace_s_per_km(run.distance_km, run.duration_s))),
    ]
    return [
        theme.section(
            ft.Column(
                [
                    ft.Row(
                        [theme.label(label), theme.name(value, size=26)],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                    for label, value in rows
                ],
                spacing=14,
            )
        )
    ]


def _pr_index(app: App, exercise_id: int, sets: list[WorkoutSet]) -> int | None:
    """Index of the exercise's all-time PR among these sets, if it is one of them."""
    pr = stats.exercise_pr(app.conn, exercise_id)
    if pr is None:
        return None
    return next((i for i, s in enumerate(sets) if s.id == pr.workout_set.id), None)
