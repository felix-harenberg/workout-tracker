from datetime import date

import flet as ft

from core import repository as repo
from core.export import export_csv, export_filename
from core.models import Workout, WorkoutType
from core.run import run_summary
from core.training import day_label, month_label, volume_label, workout_title
from ui import theme
from ui.app import App


def workout_list_view(app: App) -> ft.View:
    today = date.today()
    content: list[ft.Control] = [theme.headline("Work", "outs")]

    workouts = repo.list_workouts(app.conn)
    if not workouts:
        content.append(theme.muted("Noch keine Workouts. Tippe auf +, um zu starten."))

    current_month = None
    for w in workouts:
        month = month_label(w.date, today)
        if month != current_month:
            content.append(ft.Container(theme.label(month), padding=ft.Padding(4, 12, 0, 0)))
            current_month = month
        # Only the newest workout of today is the one that is running.
        content.append(_workout_card(app, w, running=w is workouts[0] and w.date == today))

    async def export(_: ft.Event) -> None:
        data = export_csv(app.conn).encode("utf-8")
        csv_file = ft.ShareFile.from_bytes(data, mime_type="text/csv", name=export_filename(today))
        await app.share.share_files([csv_file], subject="Workout Tracker Backup")

    return theme.view(
        "/",
        content,
        bar=theme.top_bar(
            None,
            [
                ft.IconButton(
                    icon=ft.Icons.INSIGHTS, tooltip="Statistik", on_click=lambda _: app.go("/stats")
                ),
                ft.IconButton(icon=ft.Icons.SHARE, tooltip="Als CSV exportieren", on_click=export),
            ],
        ),
        scroll=ft.ScrollMode.AUTO,
        floating_action_button=theme.fab(lambda _: app.go("/workout/new"), "Neues Workout"),
    )


def _workout_card(app: App, workout: Workout, running: bool) -> ft.Control:
    day = day_label(workout.date, date.today())
    return theme.glass_card(
        ft.Column(
            [
                theme.label(
                    f"{day} · läuft" if running else day,
                    color=theme.VIOLET_LIGHT if running else theme.TEXT_MUTED,
                ),
                theme.name(workout_title(workout)),
                theme.muted(_summary(app, workout)),
            ],
            spacing=4,
        ),
        on_click=lambda _: app.go(f"/workout/{workout.id}"),
        highlight=running,
    )


def _summary(app: App, workout: Workout) -> str:
    if workout.type == WorkoutType.RUN:
        run = repo.get_run(app.conn, workout.id)
        if run is not None:
            return run_summary(run.distance_km, run.duration_s)
    return volume_label(*repo.workout_volume(app.conn, workout.id))
