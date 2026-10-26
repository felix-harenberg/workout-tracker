"""Bodyweight: the weight page on the start screen and the weigh-in screen.

Layout follows docs/design/fortschritt.html on the ideas/design branch.
"""

from datetime import date

import flet as ft

from core import bodyweight as bw
from core.training import day_label, format_weight, parse_weight
from ui import theme
from ui.app import App
from ui.charts import date_line_chart


def weight_page(app: App) -> list[ft.Control]:
    """Controls of the "Gewicht" page: current weight, distance to goal, chart, history."""
    controls: list[ft.Control] = [theme.headline("", "Gewicht")]
    latest = bw.latest_weight(app.conn)
    if latest is None:
        controls.append(theme.muted("Noch kein Gewicht eingetragen. Tippe auf + GEWICHT."))
        return controls

    goal = bw.get_goal(app.conn)
    day, kg = latest
    controls.append(
        theme.glass_card(
            ft.Column(
                [
                    theme.label(f"Körpergewicht · {day_label(day, date.today())}"),
                    ft.Row(
                        [
                            ft.Text(
                                format_weight(kg),
                                size=64,
                                color=theme.TEXT,
                                style=ft.TextStyle(font_family=theme.TITLE_FONT, height=1.1),
                            ),
                            ft.Text("kg", size=22, color=theme.TEXT_MUTED),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        spacing=8,
                    ),
                    ft.Text(
                        bw.goal_label(kg, goal),
                        size=17,
                        color=theme.VIOLET_LIGHT if goal is not None else theme.TEXT_MUTED,
                        style=ft.TextStyle(font_family=theme.MEDIUM_FONT),
                    ),
                ],
                spacing=4,
            ),
            highlight=True,
        )
    )

    def pick_period(period: str) -> None:
        app.weight_period = period
        app.render()

    controls.append(
        ft.Row(
            [_period_pill(p, p == app.weight_period, pick_period) for p in bw.PERIODS],
            spacing=8,
        )
    )
    points = bw.list_weights(app.conn, since=bw.period_start(app.weight_period, date.today()))
    controls.append(
        theme.glass_card(
            date_line_chart(points, lambda v: f"{format_weight(v)} kg", goal=goal, color=theme.TEXT)
            if len(points) >= 1
            else theme.muted("Keine Einträge in diesem Zeitraum.")
        )
    )

    history = list(reversed(bw.list_weights(app.conn)))[:6]
    controls.append(ft.Container(theme.label("Verlauf"), padding=ft.Padding(4, 12, 0, 0)))
    controls.append(
        theme.glass_list(
            [
                theme.list_row(
                    f"{format_weight(entry_kg)} kg",
                    day_label(entry_day, date.today()),
                    on_click=lambda _, d=entry_day, k=entry_kg: _confirm_delete(app, d, k),
                    trailing=ft.Icon(ft.Icons.DELETE_OUTLINE, color=theme.TEXT_MUTED, size=20),
                )
                for entry_day, entry_kg in history
            ]
        )
    )
    return controls


def _period_pill(period: str, active: bool, on_pick) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            period,
            size=15,
            color=ft.Colors.WHITE if active else theme.TEXT_MUTED,
            style=ft.TextStyle(font_family=theme.MEDIUM_FONT),
        ),
        padding=ft.Padding(16, 8, 16, 8),
        border_radius=999,
        bgcolor=theme.VIOLET if active else ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
        border=None if active else ft.Border.all(1, theme.GLASS_BORDER),
        on_click=lambda _: on_pick(period),
        ink=True,
    )


def _confirm_delete(app: App, day: date, kg: float) -> None:
    def delete(_: ft.Event) -> None:
        app.page.pop_dialog()
        bw.delete_weight(app.conn, day)
        app.render()

    app.page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Eintrag löschen?"),
            content=ft.Text(f"{format_weight(kg)} kg vom {day.strftime('%d.%m.%Y')}"),
            actions=[
                ft.TextButton(content="Abbrechen", on_click=lambda _: app.page.pop_dialog()),
                ft.TextButton(content="Löschen", on_click=delete),
            ],
        )
    )


def weigh_view(app: App) -> ft.View:
    """Weigh-in: prefilled with the last value, so usually just ±0.1 and save."""
    today = date.today()
    latest = bw.latest_weight(app.conn)
    goal = bw.get_goal(app.conn)
    start = latest[1] if latest else goal

    field = theme.text_field(
        value=format_weight(start) if start else "",
        hint_text="kg",
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.CENTER,
        text_style=ft.TextStyle(font_family=theme.TITLE_FONT, size=56),
        suffix=ft.Text("kg", size=20, color=theme.TEXT_MUTED),
    )

    def step(delta: float) -> None:
        field.value = bw.step_bodyweight(field.value, delta)
        field.update()

    def step_button(delta: float) -> ft.Container:
        text = f"+{format_weight(delta)}" if delta > 0 else f"−{format_weight(-delta)}"
        return ft.Container(
            content=ft.Text(text, size=17, color=theme.TEXT, text_align=ft.TextAlign.CENTER),
            expand=True,
            height=48,
            alignment=ft.Alignment.CENTER,
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
            border=ft.Border.all(1, theme.GLASS_BORDER),
            on_click=lambda _: step(delta),
            ink=True,
        )

    def save(_: ft.Event) -> None:
        try:
            kg = parse_weight(field.value)
        except ValueError:
            kg = None
        if not kg:
            app.show_error("Bitte ein Gewicht eingeben.")
            return
        bw.log_weight(app.conn, today, kg)
        app.home_tab = 1
        app.back()

    controls: list[ft.Control] = [
        theme.headline("", "Wiegen", overline=day_label(today, today)),
        theme.glass_card(
            ft.Column(
                [
                    field,
                    ft.Row([step_button(d) for d in (-0.5, -0.1, 0.1, 0.5)], spacing=8),
                ],
                spacing=12,
            )
        ),
    ]
    if latest:
        last_day, last_kg = latest
        note = (
            f"Heute schon eingetragen: {format_weight(last_kg)} kg. Speichern ersetzt den Wert."
            if last_day == today
            else f"Letztes Mal: {format_weight(last_kg)} kg · {day_label(last_day, today)}"
        )
        controls.append(theme.muted(note, size=15))

    controls.append(
        theme.glass_list(
            [
                theme.list_row(
                    "Ziel",
                    f"{format_weight(goal)} kg" if goal is not None else "Noch kein Ziel",
                    on_click=lambda _: _goal_dialog(app),
                    trailing=ft.Text("ändern ›", size=15, color=theme.VIOLET_LIGHT),
                )
            ]
        )
    )
    controls.append(theme.primary_button("Speichern", save))

    return theme.view(
        "/weight/new", controls, bar=theme.top_bar(app.back), scroll=ft.ScrollMode.AUTO
    )


def _goal_dialog(app: App) -> None:
    goal = bw.get_goal(app.conn)
    field = theme.text_field(
        value=format_weight(goal) if goal is not None else "",
        label="Zielgewicht (kg)",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
    )

    def save(_: ft.Event) -> None:
        try:
            kg = parse_weight(field.value)
        except ValueError:
            kg = None
        if not kg:
            app.show_error("Bitte ein Zielgewicht eingeben.")
            return
        bw.set_goal(app.conn, kg)
        app.page.pop_dialog()
        app.render()

    def remove(_: ft.Event) -> None:
        bw.set_goal(app.conn, None)
        app.page.pop_dialog()
        app.render()

    app.page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("Zielgewicht"),
            content=field,
            actions=[
                ft.TextButton(content="Entfernen", on_click=remove),
                ft.TextButton(content="Abbrechen", on_click=lambda _: app.page.pop_dialog()),
                ft.TextButton(content="Speichern", on_click=save),
            ],
        )
    )
