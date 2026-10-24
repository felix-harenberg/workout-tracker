from datetime import date

import flet as ft

from core import repository as repo
from core.export import export_csv, export_filename
from core.models import Workout, WorkoutType
from core.run import run_summary
from core.training import format_date, workout_title
from ui.app import App


def workout_list_view(app: App) -> ft.View:
    workouts = repo.list_workouts(app.conn)

    def open_workout(workout_id: int) -> None:
        app.go(f"/workout/{workout_id}")

    if workouts:
        content: list[ft.Control] = [
            ft.Card(
                content=ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.DIRECTIONS_RUN
                        if w.type == WorkoutType.RUN
                        else ft.Icons.FITNESS_CENTER
                    ),
                    title=ft.Text(workout_title(w)),
                    subtitle=ft.Text(_subtitle(app, w)),
                    on_click=lambda _, wid=w.id: open_workout(wid),
                )
            )
            for w in workouts
        ]
    else:
        content = [ft.Text("Noch keine Workouts. Tippe auf +, um zu starten.")]

    async def export(_: ft.Event) -> None:
        data = export_csv(app.conn).encode("utf-8")
        csv_file = ft.ShareFile.from_bytes(
            data, mime_type="text/csv", name=export_filename(date.today())
        )
        await app.share.share_files([csv_file], subject="Workout Tracker Backup")

    return ft.View(
        route="/",
        appbar=ft.AppBar(
            title=ft.Text("Workouts"),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.INSIGHTS, tooltip="Statistik", on_click=lambda _: app.go("/stats")
                ),
                ft.IconButton(icon=ft.Icons.SHARE, tooltip="Als CSV exportieren", on_click=export),
            ],
        ),
        controls=content,
        scroll=ft.ScrollMode.AUTO,
        floating_action_button=ft.FloatingActionButton(
            icon=ft.Icons.ADD, tooltip="Neues Workout", on_click=lambda _: app.go("/workout/new")
        ),
    )


def _subtitle(app: App, workout: Workout) -> str:
    if workout.type == WorkoutType.RUN:
        run = repo.get_run(app.conn, workout.id)
        if run is not None:
            return f"{format_date(workout.date)}  ·  {run_summary(run.distance_km, run.duration_s)}"
    return format_date(workout.date)
