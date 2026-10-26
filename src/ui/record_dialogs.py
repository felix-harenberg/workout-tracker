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
    """Centered glass card over the dimmed set screen; violet glow, or plain for a warning."""

    def centered(text: str, size: int, color: str, font: str | None = None, **style) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            color=color,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(font_family=font, **style),
        )

    glow = ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.8, theme.VIOLET))
    card = ft.Container(
        padding=ft.Padding(24, 30, 24, 24),
        border_radius=26,
        bgcolor=ft.Colors.with_opacity(0.85, "#140C1E"),
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(0.25, ft.Colors.WHITE)
            if warn
            else ft.Colors.with_opacity(0.55, theme.VIOLET),
        ),
        shadow=None
        if warn
        else ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.35, theme.VIOLET)),
        blur=24,
        content=ft.Column(
            [
                centered(
                    kicker.upper(),
                    14,
                    theme.TEXT_MUTED if warn else theme.VIOLET_LIGHT,
                    theme.STRONG_FONT,
                    letter_spacing=3,
                ),
                ft.Container(height=6),
                centered(big, 60, theme.TEXT, theme.TITLE_FONT, height=1.15, shadow=glow),
                centered(exercise_name, 18, theme.TEXT_MUTED, theme.MEDIUM_FONT),
                centered(detail, 15, theme.TEXT_MUTED),
                ft.Container(height=14),
                centered(line, 20, theme.TEXT, theme.STRONG_FONT, height=1.35),
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


def _button(text: str, on_click: Callable, main: bool) -> ft.Container:
    """Equal-width action: violet for the main one, outlined for the other."""
    return ft.Container(
        content=ft.Text(
            text.upper(),
            size=15,
            color=ft.Colors.WHITE if main else theme.TEXT,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(font_family=theme.STRONG_FONT, letter_spacing=1),
        ),
        expand=True,
        padding=ft.Padding(0, 15, 0, 15),
        border_radius=14,
        bgcolor=theme.VIOLET if main else None,
        border=None if main else ft.Border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
        shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.5, theme.VIOLET))
        if main
        else None,
        on_click=on_click,
        ink=True,
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
        [_button("Weiter", close, main=True)],
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
            [_button("Korrigieren", correct, main=False), _button("Stimmt so", confirm, main=True)],
            warn=True,
        )
    )
