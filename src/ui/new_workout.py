from datetime import date

import flet as ft

from core import repository as repo
from core.templates import workout_templates
from core.training import day_label
from ui import theme
from ui.app import App


def new_workout_view(app: App) -> ft.View:
    # Runs are no longer logged here (watch + Strava do that); existing runs stay viewable.
    name_field = theme.text_field(label="Name (optional)", hint_text="z.B. Chestday")

    def start(name: str) -> None:
        workout = repo.create_workout(app.conn, name.strip(), date.today())
        app.go(f"/workout/{workout.id}")

    name_field.on_submit = lambda _: start(name_field.value or "")

    controls: list[ft.Control] = [
        theme.headline("Neues Workout"),
        name_field,
        theme.primary_button("Starten", lambda _: start(name_field.value or "")),
    ]

    templates = workout_templates(app.conn)
    if templates:
        controls.append(
            ft.Container(theme.label("Wie letztes Mal"), padding=ft.Padding(4, 16, 0, 0))
        )
        for t in templates:
            exercises = f"{t.exercise_count} {'Übung' if t.exercise_count == 1 else 'Übungen'}"
            last = day_label(t.last_date, date.today())
            last = last.lower() if last in ("Heute", "Gestern") else last
            controls.append(
                theme.glass_card(
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        t.name,
                                        size=18,
                                        color=theme.TEXT,
                                        style=ft.TextStyle(font_family=theme.STRONG_FONT),
                                    ),
                                    ft.Text(
                                        f"zuletzt {last}  ·  {exercises}",
                                        color=theme.TEXT_MUTED,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.REPLAY, color=theme.VIOLET_LIGHT),
                        ]
                    ),
                    on_click=lambda _, name=t.name: start(name),
                )
            )

    return theme.view(
        "/workout/new",
        controls,
        appbar=theme.app_bar(),
        scroll=ft.ScrollMode.AUTO,
    )
