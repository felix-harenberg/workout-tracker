import flet as ft

from core import repository as repo
from core import stats
from core.run import format_pace
from core.training import format_set
from ui.app import App
from ui.charts import date_line_chart, week_bar_chart

WEEKS_SHOWN = 12


def stats_view(app: App) -> ft.View:
    weeks = stats.weekly_volume(app.conn)[-WEEKS_SHOWN:]
    week_bars = [
        (
            w.week_start,
            w.sets,
            f"KW {w.week_start.isocalendar().week}: {w.sets} Sätze\n"
            f"{stats.format_tonnage(w.tonnage_kg)}",
        )
        for w in weeks
    ]

    exercise_tiles: list[ft.Control] = []
    for exercise in repo.list_exercises(app.conn):
        pr = stats.exercise_pr(app.conn, exercise.id)
        if pr is None:
            subtitle = "Nur Körpergewicht"
        else:
            subtitle = (
                f"1RM {stats.format_1rm(pr.best_1rm)}  ·  schwerster Satz "
                f"{format_set(pr.heaviest_set)}"
            )
        exercise_tiles.append(
            ft.ListTile(
                title=ft.Text(exercise.name),
                subtitle=ft.Text(subtitle),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT) if pr else None,
                on_click=(lambda _, eid=exercise.id: app.go(f"/stats/exercise/{eid}"))
                if pr
                else None,
            )
        )

    return ft.View(
        route="/stats",
        appbar=ft.AppBar(title=ft.Text("Statistik")),
        controls=[
            _section("Sätze pro Woche"),
            week_bar_chart(week_bars),
            _section("Lauf-Pace", "tiefer = schneller"),
            date_line_chart(stats.pace_history(app.conn), format_pace),
            _section("Übungen"),
            *(exercise_tiles or [ft.Text("Noch keine Übungen.", color=ft.Colors.GREY)]),
        ],
        scroll=ft.ScrollMode.AUTO,
    )


def _section(title: str, hint: str = "") -> ft.Control:
    controls: list[ft.Control] = [ft.Text(title, size=18, weight=ft.FontWeight.BOLD)]
    if hint:
        controls.append(ft.Text(hint, size=12, color=ft.Colors.GREY))
    return ft.Row(controls, vertical_alignment=ft.CrossAxisAlignment.END)
