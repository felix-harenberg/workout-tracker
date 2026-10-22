from datetime import date

import flet as ft

from core import repository as repo
from core.models import Workout
from core.training import date_from_picker, format_date
from ui.app import App


def edit_workout_view(app: App, workout: Workout) -> ft.View:
    selected_date = workout.date

    name_field = ft.TextField(label="Name (optional)", value=workout.name)
    notes_field = ft.TextField(label="Notizen", value=workout.notes, multiline=True, min_lines=3)
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

    def save(_: ft.Event) -> None:
        repo.update_workout(
            app.conn,
            workout.id,
            name=(name_field.value or "").strip(),
            workout_date=selected_date,
            notes=(notes_field.value or "").strip(),
        )
        app.go(f"/workout/{workout.id}")

    return ft.View(
        route=f"/workout/{workout.id}/edit",
        appbar=ft.AppBar(title=ft.Text("Workout bearbeiten")),
        controls=[
            name_field,
            ft.Row([ft.Text("Datum"), date_button]),
            notes_field,
            ft.Button(content="Speichern", on_click=save),
        ],
        scroll=ft.ScrollMode.AUTO,
    )
