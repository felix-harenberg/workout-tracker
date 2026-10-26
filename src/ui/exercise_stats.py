import flet as ft

from core import stats
from core.models import Exercise
from core.training import format_date, format_set, format_weight
from ui.app import App
from ui.charts import date_line_chart


def exercise_stats_view(app: App, exercise: Exercise) -> ft.View:
    pr = stats.exercise_pr(app.conn, exercise.id)
    controls: list[ft.Control] = [
        ft.Text("Schwerstes Gewicht pro Training", size=18, weight=ft.FontWeight.BOLD),
        date_line_chart(
            stats.max_weight_history(app.conn, exercise.id), lambda kg: f"{format_weight(kg)} kg"
        ),
    ]
    if pr is not None:
        controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.EMOJI_EVENTS),
                title=ft.Text(f"PR  {format_set(pr.workout_set)}"),
                subtitle=ft.Text(format_date(pr.date)),
            )
        )

    return ft.View(
        route=f"/stats/exercise/{exercise.id}",
        appbar=ft.AppBar(title=ft.Text(exercise.name)),
        controls=controls,
        scroll=ft.ScrollMode.AUTO,
    )
