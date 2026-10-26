from datetime import date

import flet as ft

from core import repository as repo
from core.templates import workout_templates
from core.training import format_date
from ui.app import App


def new_workout_view(app: App) -> ft.View:
    # Runs are no longer logged here (watch + Strava do that); existing runs stay viewable.
    name_field = ft.TextField(label="Name (optional)", hint_text="z.B. Chestday")

    def start(name: str) -> None:
        workout = repo.create_workout(app.conn, name.strip(), date.today())
        app.go(f"/workout/{workout.id}")

    name_field.on_submit = lambda _: start(name_field.value or "")

    templates = workout_templates(app.conn)
    template_controls: list[ft.Control] = []
    if templates:
        template_controls = [
            ft.Divider(),
            ft.Text("Wie letztes Mal", size=18, weight=ft.FontWeight.BOLD),
            *(
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.REPLAY),
                        title=ft.Text(t.name),
                        subtitle=ft.Text(
                            f"zuletzt {format_date(t.last_date)}  ·  "
                            f"{t.exercise_count} {'Übung' if t.exercise_count == 1 else 'Übungen'}"
                        ),
                        on_click=lambda _, name=t.name: start(name),
                    )
                )
                for t in templates
            ),
        ]

    return ft.View(
        route="/workout/new",
        appbar=ft.AppBar(title=ft.Text("Neues Workout")),
        controls=[
            name_field,
            ft.Button(content="Starten", on_click=lambda _: start(name_field.value or "")),
            *template_controls,
        ],
        scroll=ft.ScrollMode.AUTO,
    )
