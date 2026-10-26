from datetime import date

import flet as ft

from core import stats
from core.models import Exercise
from core.training import day_label, format_set, format_weight
from ui import theme
from ui.app import App
from ui.charts import date_line_chart


def exercise_stats_view(app: App, exercise: Exercise) -> ft.View:
    pr = stats.exercise_pr(app.conn, exercise.id)
    controls: list[ft.Control] = [theme.title_headline(exercise.name)]
    if pr is not None:
        controls.append(
            theme.glass_card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.VIOLET_LIGHT, size=32),
                        ft.Column(
                            [
                                theme.label("PR", color=theme.VIOLET_LIGHT),
                                theme.name(format_set(pr.workout_set), size=26),
                                theme.muted(day_label(pr.date, date.today()), size=15),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=16,
                ),
                highlight=True,
            )
        )
    controls.append(
        theme.glass_card(
            ft.Column(
                [
                    theme.label("Schwerstes Gewicht pro Training"),
                    date_line_chart(
                        stats.max_weight_history(app.conn, exercise.id),
                        lambda kg: f"{format_weight(kg)} kg",
                    ),
                ],
                spacing=16,
            )
        )
    )

    return theme.view(
        f"/stats/exercise/{exercise.id}",
        controls,
        bar=theme.top_bar(app.back),
        scroll=ft.ScrollMode.AUTO,
    )
