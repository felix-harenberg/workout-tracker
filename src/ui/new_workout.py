from datetime import date

import flet as ft

from core import repository as repo
from ui.app import App


def new_workout_view(app: App) -> ft.View:
    # Runs are no longer logged here (watch + Strava do that); existing runs stay viewable.
    name_field = ft.TextField(label="Name (optional)", hint_text="z.B. Chestday", autofocus=True)

    def start(_: ft.Event) -> None:
        workout = repo.create_workout(app.conn, (name_field.value or "").strip(), date.today())
        app.go(f"/workout/{workout.id}")

    name_field.on_submit = start

    return ft.View(
        route="/workout/new",
        appbar=ft.AppBar(title=ft.Text("Neues Workout")),
        controls=[name_field, ft.Button(content="Starten", on_click=start)],
    )
