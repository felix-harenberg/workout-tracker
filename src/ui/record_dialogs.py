"""Dialogs for a new record and for a jump that looks like a typo.

Layout follows docs/design/momente-und-icon.html on the ideas/design branch.
"""

import asyncio
from collections.abc import Callable
from datetime import date

import flet as ft

from core.records import RecordCheck, pick_quote, suspicious_message
from core.training import day_label, format_set, format_weight_reps
from ui import theme
from ui.app import App

RECORD_SECONDS = 4  # the record dialog closes itself after this


def _overlay(
    kicker: str,
    big: str,
    exercise_name: str,
    detail: str,
    line: str,
    buttons: list[ft.Control],
    warn: bool = False,
) -> ft.AlertDialog:
    """Centered black card over the dimmed set screen; blue frame, or grey for a warning.

    The set is big in the wide sans, the line below it in the curly serif, like a quote
    on the blog.
    """

    def centered(text: str, size: int, color: str, font: str | None = None, **style) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            color=color,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(font_family=font, **style),
        )

    card = ft.Container(
        padding=ft.Padding(24, 30, 24, 24),
        bgcolor=theme.BG,
        border=ft.Border.all(1, theme.LINE if warn else theme.BLUE),
        content=ft.Column(
            [
                centered(
                    kicker.upper(),
                    13,
                    theme.TEXT_MUTED if warn else theme.BLUE,
                    theme.MONO_FONT,
                    letter_spacing=2,
                ),
                ft.Container(height=8),
                centered(big, 40, theme.TEXT, theme.NAME_FONT, height=1.1),
                ft.Container(height=4),
                centered(exercise_name.upper(), 14, theme.TEXT_MUTED, theme.MONO_FONT),
                centered(detail, 13, theme.DIM, theme.MONO_FONT),
                ft.Container(height=14),
                centered(line, 28, theme.TEXT, theme.TITLE_FONT, height=1.15),
                ft.Container(height=14),
                ft.Row(buttons, spacing=10),
            ],
            tight=True,
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return ft.AlertDialog(
        modal=True,
        bgcolor=ft.Colors.TRANSPARENT,
        elevation=0,
        content_padding=0,
        inset_padding=ft.Padding(20, 24, 20, 24),
        barrier_color=ft.Colors.with_opacity(0.7, theme.BG),
        content=card,
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

    dialog = _overlay(
        "Neuer Rekord",
        format_weight_reps(weight_kg, reps),
        exercise_name,
        before,
        pick_quote(),
        [theme.dialog_button("Weiter", close, "main")],
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
        _overlay(
            "Moment mal",
            format_weight_reps(weight_kg, reps),
            exercise_name,
            f"bisher bestes: {format_set(check.previous_best)}",
            suspicious_message(weight_kg, check.previous_best.weight_kg),
            [
                theme.dialog_button("Korrigieren", correct),
                theme.dialog_button("Stimmt so", confirm, "main"),
            ],
            warn=True,
        )
    )
