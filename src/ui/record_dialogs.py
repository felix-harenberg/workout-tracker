"""Dialogs for a new record and for a jump that looks like a typo."""

import asyncio
from collections.abc import Callable
from datetime import date

import flet as ft

from core.records import RecordCheck, pick_quote, suspicious_message
from core.training import day_label, format_set, format_weight_reps
from ui import theme
from ui.app import App

RECORD_SECONDS = 4  # the record dialog closes itself after this


def _dialog(content: list[ft.Control], actions: list[ft.Control]) -> ft.AlertDialog:
    return ft.AlertDialog(
        modal=True,
        bgcolor="#15111D",
        shape=ft.RoundedRectangleBorder(radius=22),
        content=ft.Column(content, tight=True, spacing=10),
        actions=actions,
        actions_alignment=ft.MainAxisAlignment.END,
    )


def _big(text: str) -> ft.Text:
    glow = ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.8, theme.VIOLET))
    return ft.Text(
        text,
        size=38,
        color=theme.TEXT,
        style=ft.TextStyle(font_family=theme.TITLE_FONT, shadow=glow),
    )


def show_record(
    app: App, exercise_name: str, weight_kg: float, reps: int, check: RecordCheck
) -> None:
    """Short and dry, closes itself after a few seconds or with "Weiter"."""
    before = ""
    if check.previous_best is not None:
        before = f"vorher {format_set(check.previous_best)}"
        if check.previous_date:
            before += f" · {day_label(check.previous_date, date.today())}"

    def close(_: ft.Event | None = None) -> None:
        if dialog.open:
            app.page.pop_dialog()

    dialog = _dialog(
        [
            theme.label("Neuer Rekord", color=theme.VIOLET_LIGHT),
            _big(format_weight_reps(weight_kg, reps)),
            theme.name(exercise_name, size=20),
            theme.muted(before, size=15),
            ft.Container(height=4),
            ft.Text(pick_quote(), size=17, italic=True, color=theme.TEXT),
        ],
        [ft.TextButton(content="Weiter", on_click=close)],
    )
    app.page.show_dialog(dialog)

    async def close_later() -> None:
        await asyncio.sleep(RECORD_SECONDS)
        close()

    app.page.run_task(close_later)


def show_suspicious(
    app: App,
    exercise_name: str,
    weight_kg: float,
    reps: int,
    check: RecordCheck,
    on_correct: Callable[[], object],
    on_confirm: Callable[[], None],
) -> None:
    """Ask before saving a set far above the previous best."""
    assert check.previous_best is not None and check.previous_best.weight_kg is not None

    def correct(_: ft.Event) -> None:
        app.page.pop_dialog()
        app.page.run_task(on_correct)

    def confirm(_: ft.Event) -> None:
        app.page.pop_dialog()
        on_confirm()

    app.page.show_dialog(
        _dialog(
            [
                theme.label("Moment mal", color=theme.DOWN_COLOR),
                _big(format_weight_reps(weight_kg, reps)),
                theme.name(exercise_name, size=20),
                theme.muted(f"bisher bestes: {format_set(check.previous_best)}", size=15),
                ft.Container(height=4),
                ft.Text(
                    suspicious_message(weight_kg, check.previous_best.weight_kg),
                    size=17,
                    color=theme.TEXT,
                ),
            ],
            [
                ft.TextButton(content="Korrigieren", on_click=correct),
                ft.TextButton(content="Stimmt so", on_click=confirm),
            ],
        )
    )
