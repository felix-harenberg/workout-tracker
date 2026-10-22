import flet as ft

from core import repository as repo
from core.training import format_date, workout_title
from ui.app import App


def workout_list_view(app: App) -> ft.View:
    workouts = repo.list_workouts(app.conn)

    def open_workout(workout_id: int) -> None:
        app.go(f"/workout/{workout_id}")

    if workouts:
        content: list[ft.Control] = [
            ft.Card(
                content=ft.ListTile(
                    title=ft.Text(workout_title(w)),
                    subtitle=ft.Text(format_date(w.date)),
                    on_click=lambda _, wid=w.id: open_workout(wid),
                )
            )
            for w in workouts
        ]
    else:
        content = [ft.Text("Noch keine Workouts. Tippe auf +, um zu starten.")]

    return ft.View(
        route="/",
        appbar=ft.AppBar(title=ft.Text("Workouts")),
        controls=content,
        scroll=ft.ScrollMode.AUTO,
        floating_action_button=ft.FloatingActionButton(
            icon=ft.Icons.ADD, tooltip="Neues Workout", on_click=lambda _: app.go("/workout/new")
        ),
    )
