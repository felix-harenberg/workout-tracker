import flet as ft

from core import repository as repo
from core import stats
from core.training import format_set
from ui.app import App
from ui.charts import week_bar_chart

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
        subtitle = f"PR {format_set(pr.workout_set)}" if pr else "Nur Körpergewicht"
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
            _section("Übungen"),
            *(exercise_tiles or [ft.Text("Noch keine Übungen.", color=ft.Colors.GREY)]),
        ],
        scroll=ft.ScrollMode.AUTO,
    )


def _section(title: str) -> ft.Control:
    return ft.Text(title, size=18, weight=ft.FontWeight.BOLD)
