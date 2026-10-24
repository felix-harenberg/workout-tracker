from datetime import date

import flet as ft

from core import repository as repo
from core.models import WorkoutType
from ui.app import App
from ui.run_fields import RunFields


def new_workout_view(app: App) -> ft.View:
    name_field = ft.TextField(label="Name (optional)", hint_text="z.B. Chestday")
    run_fields = RunFields(app)
    run_section = ft.Column(run_fields.controls, visible=False)
    start_button = ft.Button(content="Starten")

    type_selector = ft.SegmentedButton(
        segments=[
            ft.Segment(
                value=WorkoutType.STRENGTH,
                label=ft.Text("Kraft"),
                icon=ft.Icon(ft.Icons.FITNESS_CENTER),
            ),
            ft.Segment(
                value=WorkoutType.RUN,
                label=ft.Text("Lauf"),
                icon=ft.Icon(ft.Icons.DIRECTIONS_RUN),
            ),
        ],
        selected=[WorkoutType.STRENGTH],
    )

    def selected_type() -> WorkoutType:
        return WorkoutType(type_selector.selected[0])

    def on_type_change(_: ft.Event) -> None:
        is_run = selected_type() == WorkoutType.RUN
        run_section.visible = is_run
        start_button.content = "Speichern" if is_run else "Starten"
        app.page.update()

    def start(_: ft.Event) -> None:
        name = (name_field.value or "").strip()
        if selected_type() == WorkoutType.RUN:
            values = run_fields.read()
            if values is None:
                return
            distance_km, duration_s = values
            workout, _ = repo.create_run(
                app.conn, name, date.today(), distance_km=distance_km, duration_s=duration_s
            )
        else:
            workout = repo.create_workout(app.conn, name, date.today())
        app.go(f"/workout/{workout.id}")

    type_selector.on_change = on_type_change
    start_button.on_click = start
    name_field.on_submit = start

    return ft.View(
        route="/workout/new",
        appbar=ft.AppBar(title=ft.Text("Neues Workout")),
        controls=[type_selector, name_field, run_section, start_button],
    )
