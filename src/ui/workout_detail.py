from datetime import date

import flet as ft

from core import repository as repo
from core import stats
from core.models import Workout, WorkoutSet, WorkoutType
from core.run import format_distance, format_duration, format_pace, pace_s_per_km
from core.templates import pending_exercises
from core.training import day_label, format_set_compact, group_sets_by_exercise, workout_title
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
    confirm_delete = ft.AlertDialog(
        modal=True,
        title=ft.Text("Workout löschen?"),
        content=ft.Text(f"„{workout_title(workout)}“ {what} gelöscht."),
        actions=[
            ft.TextButton(content="Abbrechen", on_click=lambda _: app.page.pop_dialog()),
            ft.TextButton(content="Löschen", on_click=delete),
        ],
    )

    return theme.view(
        route,
        controls,
        bar=theme.top_bar(
            app.back,
            [
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    tooltip="Bearbeiten",
                    on_click=lambda _: app.go(f"{route}/edit"),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Löschen",
                    on_click=lambda _: app.page.show_dialog(confirm_delete),
                ),
            ],
        ),
        scroll=ft.ScrollMode.AUTO,
        floating_action_button=None
        if is_run
        else theme.fab(lambda _: app.go(f"{route}/add-exercise"), "Übung hinzufügen"),
    )


def _strength_controls(app: App, workout: Workout) -> list[ft.Control]:
    route = f"/workout/{workout.id}"
    groups = group_sets_by_exercise(repo.list_sets(app.conn, workout.id))
    # Only today's workout offers last time's exercises; old ones show what was done.
    pending = pending_exercises(app.conn, workout) if workout.date == date.today() else []
    if not groups and not pending:
        return [theme.muted("Noch keine Übungen. Tippe auf +, um eine hinzuzufügen.")]

    controls: list[ft.Control] = []
    for exercise_id, sets in groups:
        exercise = repo.get_exercise(app.conn, exercise_id)
        assert exercise is not None
        controls.append(
            theme.glass_card(
                ft.Column(
                    [
                        theme.name(exercise.name, size=22),
                        theme.chips(
                            [format_set_compact(s) for s in sets],
                            highlighted=_pr_index(app, exercise_id, sets),
                        ),
                    ],
                    spacing=10,
                ),
                on_click=lambda _, eid=exercise_id: app.go(f"{route}/exercise/{eid}"),
            )
        )

    if pending:
        controls.append(
            ft.Container(theme.label("Vom letzten Mal"), padding=ft.Padding(4, 12, 0, 0))
        )
    for p in pending:
        controls.append(
            ft.Container(
                theme.glass_card(
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    theme.name(p.exercise.name, size=22),
                                    theme.muted(
                                        "  ·  ".join(format_set_compact(s) for s in p.last_sets)
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=theme.VIOLET_LIGHT, size=32),
                        ]
                    ),
                    on_click=lambda _, eid=p.exercise.id: app.go(f"{route}/exercise/{eid}"),
                ),
                opacity=0.7,  # not done yet
            )
        )
    return controls


def _run_controls(app: App, workout: Workout) -> list[ft.Control]:
    run = repo.get_run(app.conn, workout.id)
    assert run is not None
    rows = [
        ("Distanz", format_distance(run.distance_km)),
        ("Dauer", format_duration(run.duration_s)),
        ("Pace", format_pace(pace_s_per_km(run.distance_km, run.duration_s))),
    ]
    return [
        theme.glass_card(
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
