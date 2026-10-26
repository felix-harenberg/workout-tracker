import flet as ft

from core import repository as repo
from core import stats
from ui import theme
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

    # Strength as simple lines (first -> best), like the progress draft; tap for the chart.
    rows: list[ft.Control] = []
    for exercise in repo.list_exercises(app.conn):
        progress = stats.progress_label(app.conn, exercise.id)
        if progress is None:
            continue  # never logged
        has_chart = stats.exercise_pr(app.conn, exercise.id) is not None
        rows.append(
            theme.list_row(
                exercise.name,
                progress,
                on_click=(lambda _, eid=exercise.id: app.go(f"/stats/exercise/{eid}"))
                if has_chart
                else None,
            )
        )

    return theme.view(
        "/stats",
        [
            theme.headline("", "Statistik"),
            theme.glass_card(
                ft.Column([theme.label("Sätze pro Woche"), week_bar_chart(week_bars)], spacing=16)
            ),
            ft.Container(
                theme.label("Kraft · erster → bester Wert"), padding=ft.Padding(4, 12, 0, 0)
            ),
            theme.glass_list(rows) if rows else theme.muted("Noch keine Übungen."),
        ],
        bar=theme.top_bar(app.back),
        scroll=ft.ScrollMode.AUTO,
    )
