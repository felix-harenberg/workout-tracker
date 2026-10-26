import flet as ft

from core import repository as repo
from core import stats
from core.training import format_set
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

    exercise_cards: list[ft.Control] = []
    for exercise in repo.list_exercises(app.conn):
        pr = stats.exercise_pr(app.conn, exercise.id)
        exercise_cards.append(
            theme.glass_card(
                ft.Row(
                    [
                        ft.Column(
                            [
                                theme.name(exercise.name, size=20),
                                theme.muted(
                                    f"PR  {format_set(pr.workout_set)}"
                                    if pr
                                    else "Nur Körpergewicht",
                                    size=15,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.TEXT_MUTED)
                        if pr
                        else ft.Container(),
                    ]
                ),
                on_click=(lambda _, eid=exercise.id: app.go(f"/stats/exercise/{eid}"))
                if pr
                else None,
                padding=14,
            )
        )

    return theme.view(
        "/stats",
        [
            theme.headline("", "Statistik"),
            theme.glass_card(
                ft.Column([theme.label("Sätze pro Woche"), week_bar_chart(week_bars)], spacing=16)
            ),
            ft.Container(theme.label("Übungen"), padding=ft.Padding(4, 12, 0, 0)),
            *(exercise_cards or [theme.muted("Noch keine Übungen.")]),
        ],
        appbar=theme.app_bar(),
        scroll=ft.ScrollMode.AUTO,
    )
