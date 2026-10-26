from datetime import date

import flet as ft

from core import repository as repo
from core.models import Workout, WorkoutType
from core.run import format_distance, format_duration, format_pace, pace_s_per_km
from core.templates import pending_exercises
from core.training import format_date, format_set, group_sets_by_exercise, workout_title
from ui.app import App


def workout_detail_view(app: App, workout: Workout) -> ft.View:
    route = f"/workout/{workout.id}"
    is_run = workout.type == WorkoutType.RUN

    controls: list[ft.Control] = [ft.Text(format_date(workout.date), color=ft.Colors.GREY)]
    if workout.notes:
        controls.append(ft.Text(workout.notes))
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

    return ft.View(
        route=route,
        appbar=ft.AppBar(
            title=ft.Text(workout_title(workout)),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.EDIT,
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
        controls=controls,
        scroll=ft.ScrollMode.AUTO,
        floating_action_button=None
        if is_run
        else ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip="Übung hinzufügen",
            on_click=lambda _: app.go(f"{route}/add-exercise"),
        ),
    )


def _strength_controls(app: App, workout: Workout) -> list[ft.Control]:
    route = f"/workout/{workout.id}"
    groups = group_sets_by_exercise(repo.list_sets(app.conn, workout.id))
    # Only today's workout offers last time's exercises; old ones show what was done.
    pending = pending_exercises(app.conn, workout) if workout.date == date.today() else []
    if not groups and not pending:
        return [ft.Text("Noch keine Übungen. Tippe auf +, um eine hinzuzufügen.")]

    controls: list[ft.Control] = []
    for exercise_id, sets in groups:
        exercise = repo.get_exercise(app.conn, exercise_id)
        assert exercise is not None
        controls.append(
            ft.Card(
                content=ft.ListTile(
                    title=ft.Text(exercise.name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(
                        "\n".join(f"Satz {s.set_number}:  {format_set(s)}" for s in sets)
                    ),
                    on_click=lambda _, eid=exercise_id: app.go(f"{route}/exercise/{eid}"),
                )
            )
        )

    if pending:
        controls.append(ft.Text("Vom letzten Mal", size=16, weight=ft.FontWeight.BOLD))
        for p in pending:
            controls.append(
                ft.Card(
                    variant=ft.CardVariant.OUTLINED,
                    content=ft.ListTile(
                        title=ft.Text(p.exercise.name),
                        subtitle=ft.Text(
                            "  ·  ".join(format_set(s) for s in p.last_sets),
                            color=ft.Colors.GREY,
                        ),
                        trailing=ft.Icon(ft.Icons.PLAY_ARROW),
                        on_click=lambda _, eid=p.exercise.id: app.go(f"{route}/exercise/{eid}"),
                    ),
                )
            )
    return controls


def _run_controls(app: App, workout: Workout) -> list[ft.Control]:
    run = repo.get_run(app.conn, workout.id)
    assert run is not None
    rows = [
        (ft.Icons.STRAIGHTEN, "Distanz", format_distance(run.distance_km)),
        (ft.Icons.TIMER_OUTLINED, "Dauer", format_duration(run.duration_s)),
        (ft.Icons.SPEED, "Pace", format_pace(pace_s_per_km(run.distance_km, run.duration_s))),
    ]
    return [
        ft.Card(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(icon),
                        title=ft.Text(label),
                        trailing=ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                    )
                    for icon, label, value in rows
                ]
            )
        )
    ]
