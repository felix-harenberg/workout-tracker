import flet as ft

from core import repository as repo
from core.models import Workout
from ui.app import App


def exercise_picker_view(app: App, workout: Workout) -> ft.View:
    route = f"/workout/{workout.id}/add-exercise"
    exercises = repo.list_exercises(app.conn)

    def open_exercise(exercise_id: int) -> None:
        app.go(f"/workout/{workout.id}/exercise/{exercise_id}")

    def add_new(_: ft.Event) -> None:
        try:
            exercise = repo.get_or_create_exercise(app.conn, name_field.value or "")
        except ValueError:
            app.show_error("Bitte einen Namen eingeben.")
            return
        open_exercise(exercise.id)

    def filter_list(_: ft.Event) -> None:
        query = (name_field.value or "").strip().casefold()
        for tile in exercise_list.controls:
            tile.visible = query in tile.data.casefold()
        exercise_list.update()

    name_field = ft.TextField(
        label="Übung suchen oder neu anlegen",
        expand=True,
        on_change=filter_list,
        on_submit=add_new,
    )
    exercise_list = ft.Column(
        [
            ft.ListTile(
                title=ft.Text(e.name),
                data=e.name,
                on_click=lambda _, eid=e.id: open_exercise(eid),
            )
            for e in exercises
        ]
    )

    return ft.View(
        route=route,
        appbar=ft.AppBar(title=ft.Text("Übung wählen")),
        controls=[
            ft.Row([name_field, ft.IconButton(icon=ft.Icons.ADD, on_click=add_new)]),
            exercise_list,
        ],
        scroll=ft.ScrollMode.AUTO,
    )
