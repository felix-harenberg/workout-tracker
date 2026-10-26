from datetime import date

import flet as ft

from core import repository as repo
from core.models import Workout, WorkoutType
from core.training import date_from_picker, format_date
from ui import theme
from ui.app import App
from ui.run_fields import RunFields


def edit_workout_view(app: App, workout: Workout) -> ft.View:
    selected_date = workout.date

    name_field = theme.text_field(label="Name (optional)", value=workout.name, text_size=18)
    notes_field = theme.text_field(
        label="Notizen", value=workout.notes, multiline=True, min_lines=3, text_size=17
    )
    date_button = ft.OutlinedButton(
        content=format_date(selected_date), icon=ft.Icons.CALENDAR_MONTH
    )

    def on_date_picked(e: ft.Event) -> None:
        nonlocal selected_date
        value = e.control.value
        if value is None:
            return
        selected_date = date_from_picker(value)
        date_button.content = format_date(selected_date)
        date_button.update()

    date_picker = ft.DatePicker(
        value=selected_date,
        first_date=date(2020, 1, 1),
        last_date=date(2100, 12, 31),
        on_change=on_date_picked,
    )
    date_button.on_click = lambda _: app.page.show_dialog(date_picker)

    run_fields = (
        RunFields(app, repo.get_run(app.conn, workout.id))
        if workout.type == WorkoutType.RUN
        else None
    )

    def save(_: ft.Event) -> None:
        if run_fields is not None:
            values = run_fields.read()
            if values is None:
                return
            distance_km, duration_s = values
            repo.update_run(app.conn, workout.id, distance_km=distance_km, duration_s=duration_s)
        repo.update_workout(
            app.conn,
            workout.id,
            name=(name_field.value or "").strip(),
            workout_date=selected_date,
            notes=(notes_field.value or "").strip(),
        )
        app.go(f"/workout/{workout.id}")

    return theme.view(
        f"/workout/{workout.id}/edit",
        [
            theme.headline("", "Bearbeiten", size=52),
            name_field,
            ft.Row([theme.label("Datum"), date_button], spacing=16),
            *(run_fields.controls if run_fields else []),
            notes_field,
            theme.primary_button("Speichern", save),
        ],
        appbar=theme.app_bar(),
        scroll=ft.ScrollMode.AUTO,
    )
