import flet as ft

from core import stats
from core.models import Exercise
from core.training import format_date, format_set
from ui.app import App
from ui.charts import date_line_chart


def exercise_stats_view(app: App, exercise: Exercise) -> ft.View:
    pr = stats.exercise_pr(app.conn, exercise.id)
    controls: list[ft.Control] = [
        ft.Text("Geschätztes 1RM", size=18, weight=ft.FontWeight.BOLD),
        date_line_chart(stats.exercise_1rm_history(app.conn, exercise.id), stats.format_1rm),
    ]
    if pr is not None:
        controls += [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.EMOJI_EVENTS),
                title=ft.Text(f"Bestes 1RM  {stats.format_1rm(pr.best_1rm)}"),
                subtitle=ft.Text(f"{format_set(pr.best_1rm_set)}, {format_date(pr.best_1rm_date)}"),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FITNESS_CENTER),
                title=ft.Text(f"Schwerster Satz  {format_set(pr.heaviest_set)}"),
                subtitle=ft.Text(format_date(pr.heaviest_date)),
            ),
            ft.Text(
                "1RM geschätzt nach Epley: Gewicht × (1 + Wdh. / 30)",
                size=12,
                color=ft.Colors.GREY,
            ),
        ]

    return ft.View(
        route=f"/stats/exercise/{exercise.id}",
        appbar=ft.AppBar(title=ft.Text(exercise.name)),
        controls=controls,
        scroll=ft.ScrollMode.AUTO,
    )
