import flet as ft

from core import repository as repo
from core.models import Workout
from core.training import format_date, format_set, group_sets_by_exercise, workout_title
from ui.app import App


def workout_detail_view(app: App, workout: Workout) -> ft.View:
    route = f"/workout/{workout.id}"
    groups = group_sets_by_exercise(repo.list_sets(app.conn, workout.id))

    controls: list[ft.Control] = [ft.Text(format_date(workout.date), color=ft.Colors.GREY)]
    if workout.notes:
        controls.append(ft.Text(workout.notes))

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

    if not groups:
        controls.append(ft.Text("Noch keine Übungen. Tippe auf +, um eine hinzuzufügen."))

    def delete(_: ft.Event) -> None:
        app.page.pop_dialog()
        repo.delete_workout(app.conn, workout.id)
        app.go("/")

    confirm_delete = ft.AlertDialog(
        modal=True,
        title=ft.Text("Workout löschen?"),
        content=ft.Text(f"„{workout_title(workout)}“ und alle Sätze werden gelöscht."),
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
        floating_action_button=ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip="Übung hinzufügen",
            on_click=lambda _: app.go(f"{route}/add-exercise"),
        ),
    )
