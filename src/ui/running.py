"""The "Laufen" page: kilometres this week against the week's goal, the runs, past weeks."""

from datetime import date, timedelta

import flet as ft

from core import run_volume as rv
from core.training import day_label
from ui import theme
from ui.app import App
from ui.charts import week_bar_chart


def running_page(app: App) -> list[ft.Control]:
    today = date.today()
    week = rv.week_start(today)
    km = rv.week_km(app.conn, week)
    goal = rv.get_goal(app.conn, week)
    kw = today.isocalendar().week

    controls: list[ft.Control] = [theme.headline("Laufen")]
    controls.append(
        theme.section(
            ft.Row(
                [
                    _week_ring(km, goal),
                    ft.Column(
                        [
                            theme.label(f"KW {kw} · Mo {week.day}.{week.month}."),
                            ft.Text(
                                rv.goal_label(km, goal),
                                size=17,
                                color=theme.BLUE if goal is not None else theme.TEXT_MUTED,
                                style=ft.TextStyle(font_family=theme.MEDIUM_FONT),
                            ),
                            theme.secondary_button(
                                "Ziel ändern" if goal else "Ziel setzen",
                                lambda _: _goal_dialog(app, week),
                            ),
                        ],
                        spacing=10,
                        expand=True,
                    ),
                ],
                spacing=20,
            ),
            highlight=True,
        )
    )

    runs = rv.runs_in_week(app.conn, week)
    controls.append(ft.Container(theme.label("Diese Woche"), padding=ft.Padding(4, 12, 0, 0)))
    controls.append(
        theme.line_list(
            [
                theme.list_row(
                    f"{rv.format_km(r.distance_km)} km",
                    day_label(r.date, today),
                    on_click=lambda _, r=r: run_dialog(app, r),
                    trailing=ft.Icon(ft.Icons.EDIT_OUTLINED, color=theme.TEXT_MUTED, size=20),
                )
                for r in runs
            ]
        )
        if runs
        else theme.muted("Noch kein Lauf diese Woche. Tippe auf + LAUF.")
    )

    weeks = rv.history(app.conn, today)
    if weeks:
        controls.append(ft.Container(theme.label("Wochen"), padding=ft.Padding(4, 12, 0, 0)))
        controls.append(
            theme.section(
                week_bar_chart(
                    [
                        (
                            w.week,
                            w.km,
                            f"KW {w.week.isocalendar().week}\n{rv.format_km(w.km)}"
                            + (f" / {rv.format_km(w.goal)} km" if w.goal else " km"),
                        )
                        for w in weeks
                    ],
                    goals=[w.goal for w in weeks],
                )
            )
        )
    return controls


def _week_ring(km: float, goal: float | None) -> ft.Control:
    """Blue ring that fills up with the week's km; the number in the middle."""
    return ft.Stack(
        [
            ft.ProgressRing(
                value=min(km / goal, 1) if goal else 0,
                width=120,
                height=120,
                stroke_width=6,
                color=theme.BLUE,
                bgcolor=theme.LINE,
            ),
            ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            rv.format_km(km),
                            size=30 if km < 100 else 24,
                            color=theme.TEXT,
                            style=ft.TextStyle(font_family=theme.NAME_FONT, height=1),
                        ),
                        theme.label(f"/ {rv.format_km(goal)} km" if goal else "km"),
                    ],
                    spacing=4,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=120,
                height=120,
                alignment=ft.Alignment.CENTER,
            ),
        ],
        width=120,
        height=120,
    )


def _km_field(value: str) -> tuple[ft.TextField, ft.Row]:
    field = theme.text_field(
        label="km",
        value=value,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_style=ft.TextStyle(font_family=theme.STRONG_FONT, size=24),
        autofocus=True,
    )
    steps = ft.Row(
        [
            theme.stepper(label, field, lambda v, d=delta: rv.step_km(v, d))
            for label, delta in (("−1", -1), ("−0.5", -0.5), ("+0.5", 0.5), ("+1", 1))
        ],
        spacing=6,
    )
    return field, steps


def _read_km(app: App, field: ft.TextField) -> float | None:
    try:
        return rv.parse_km(field.value)
    except ValueError:
        app.show_error("Bitte Kilometer eingeben.")
        return None


def run_dialog(app: App, run: rv.RunEntry | None = None) -> None:
    """Log a run (today by default) or correct and delete one."""
    today = date.today()
    field, steps = _km_field(rv.format_km(run.distance_km) if run else "")
    chosen = run.date if run else today
    # Runs are logged on the day or soon after; an older run keeps its own date as a pill.
    days = [today, today - timedelta(days=1), today - timedelta(days=2)]
    if chosen not in days:
        days.append(chosen)
    pills = ft.Row(spacing=6, wrap=True, run_spacing=6)

    def show_pills() -> None:
        pills.controls = [_day_pill(d, d == chosen, today, pick) for d in days]

    def pick(day: date) -> None:
        nonlocal chosen
        chosen = day
        show_pills()
        pills.update()

    show_pills()

    def save(_: ft.Event) -> None:
        km = _read_km(app, field)
        if km is None:
            return
        if run:
            rv.update_run(app.conn, run.id, chosen, km)
        else:
            rv.add_run(app.conn, chosen, km)
        app.page.pop_dialog()
        app.render()

    def delete(_: ft.Event) -> None:
        assert run is not None
        rv.delete_run(app.conn, run.id)
        app.page.pop_dialog()
        app.render()

    second_row = [theme.dialog_button("Abbrechen", lambda _: app.page.pop_dialog())]
    if run:
        second_row.append(theme.dialog_button("Löschen", delete, "danger_outline"))
    app.page.show_dialog(
        theme.dialog(
            "Laufen",
            "Lauf ändern" if run else "Lauf eintragen",
            [field, steps, pills],
            [
                ft.Row([theme.dialog_button("Speichern", save, "main")]),
                ft.Row(second_row, spacing=10),
            ],
        )
    )


def _day_pill(day: date, active: bool, today: date, on_pick) -> ft.Container:
    return ft.Container(
        ft.Text(
            day_label(day, today),
            size=13,
            color=theme.TEXT if active else theme.TEXT_MUTED,
            style=ft.TextStyle(font_family=theme.MONO_FONT),
        ),
        padding=ft.Padding(10, 7, 10, 7),
        bgcolor=theme.BLUE if active else None,
        border=ft.Border.all(1, theme.BLUE if active else theme.LINE),
        on_click=lambda _: on_pick(day),
        ink=True,
    )


def _goal_dialog(app: App, week: date) -> None:
    """Set this week's goal; prefilled with the current one or last goal + 10 %."""
    current = rv.get_goal(app.conn, week)
    suggestion = rv.suggest_goal(app.conn, week)
    field, steps = _km_field(rv.format_km(current if current else suggestion))

    def save(_: ft.Event) -> None:
        km = _read_km(app, field)
        if km is None:
            return
        rv.set_goal(app.conn, week, km)
        app.page.pop_dialog()
        app.render()

    hint = (
        f"Vorschlag: {rv.format_km(suggestion)} km, dein letztes Ziel + 10 %."
        if suggestion != rv.FIRST_GOAL_KM or current
        else "Vorschlag zum Start: 20 km."
    )
    app.page.show_dialog(
        theme.dialog(
            f"KW {week.isocalendar().week}",
            "Wochenziel",
            [field, steps, theme.muted(hint)],
            [
                ft.Row([theme.dialog_button("Speichern", save, "main")]),
                ft.Row([theme.dialog_button("Abbrechen", lambda _: app.page.pop_dialog())]),
            ],
        )
    )
