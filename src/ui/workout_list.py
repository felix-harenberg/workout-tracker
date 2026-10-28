from datetime import date

import flet as ft

from core import bodyweight as bw
from core import repository as repo
from core.export import export_csv, export_filename
from core.models import Workout, WorkoutType
from core.run import run_summary
from core.training import (
    count_in_month,
    day_label,
    month_label,
    short_month,
    volume_label,
    workout_title,
)
from ui import theme
from ui.app import App
from ui.weight import weight_page

TABS = ["Training", "Gewicht"]


def workout_list_view(app: App) -> ft.View:
    """Start screen: two pages to swipe between, Training and Gewicht."""
    today = date.today()
    pages = [_page(_training_page(app, today)), _page(weight_page(app))]
    fab_holder = ft.Container(_fab(app, app.home_tab))
    tab_row = ft.Row(spacing=18)

    def show_tabs() -> None:
        tab_row.controls = [_tab(name, i == app.home_tab, i, go_to) for i, name in enumerate(TABS)]

    async def go_to(index: int) -> None:
        await page_view.go_to_page(
            index, animation_duration=280, animation_curve=ft.AnimationCurve.EASE_OUT
        )

    def on_change(e: ft.Event) -> None:
        app.home_tab = int(e.data)
        show_tabs()
        fab_holder.content = _fab(app, app.home_tab)
        tab_row.update()
        fab_holder.update()

    page_view = ft.PageView(pages, selected_index=app.home_tab, expand=True, on_change=on_change)
    show_tabs()

    async def export(_: ft.Event) -> None:
        files = [
            ft.ShareFile.from_bytes(
                export_csv(app.conn).encode("utf-8"),
                mime_type="text/csv",
                name=export_filename(today),
            ),
            ft.ShareFile.from_bytes(
                bw.export_bodyweight_csv(app.conn).encode("utf-8"),
                mime_type="text/csv",
                name=f"bodyweight-{today.isoformat()}.csv",
            ),
        ]
        await app.share.share_files(files, subject="Workout Tracker Backup")

    return theme.view(
        "/",
        [page_view],
        bar=theme.top_bar(
            None,
            [
                theme.icon_button(ft.Icons.INSIGHTS, lambda _: app.go("/stats"), "Statistik"),
                theme.icon_button(ft.Icons.SHARE, export, "Als CSV exportieren"),
            ],
            left=tab_row,
        ),
        fab=fab_holder,
        edge_to_edge=True,
    )


def _page(controls: list[ft.Control]) -> ft.Container:
    """One swipe page: full width with its own side padding, so it slides out over the
    screen edge; scrolls on its own and leaves room for the floating button."""
    return ft.Container(
        ft.Column(
            [*controls, ft.Container(height=88)],
            spacing=12,
            scroll=ft.ScrollMode.HIDDEN,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=ft.Padding(theme.SIDE_PADDING, 0, theme.SIDE_PADDING, 0),
    )


def _tab(name: str, active: bool, index: int, on_select) -> ft.Container:
    """Tab label: bright with a blue line when active, grey otherwise. Tap to switch."""

    async def select(_: ft.Event) -> None:
        await on_select(index)

    return ft.Container(
        content=ft.Column(
            [
                theme.label(name, color=theme.TEXT if active else theme.TEXT_MUTED),
                ft.Container(
                    height=2,
                    width=28,
                    bgcolor=theme.BLUE if active else ft.Colors.TRANSPARENT,
                ),
            ],
            spacing=6,
            tight=True,
        ),
        padding=ft.Padding(0, 10, 0, 0),
        on_click=select,
    )


def _fab(app: App, tab: int) -> ft.Control:
    if tab == 1:
        return theme.fab(lambda _: app.go("/weight/new"), "Gewicht eintragen", "Gewicht")
    return theme.fab(lambda _: app.go("/workout/new"), "Neues Workout")


def _training_page(app: App, today: date) -> list[ft.Control]:
    workouts = repo.list_workouts(app.conn)
    ring = theme.count_ring(
        count_in_month([w.date for w in workouts], today), f"im {short_month(today)}"
    )
    content: list[ft.Control] = [theme.headline("Workouts", ring=ring)]
    if not workouts:
        content.append(theme.muted("Noch keine Workouts. Tippe auf +, um zu starten."))

    # The newest workout of today is the one that is running (a workout dated in the
    # future can sit above it in the list).
    running_id = next((w.id for w in workouts if w.date == today), None)
    current_month = None
    for w in workouts:
        month = month_label(w.date, today)
        if month != current_month:
            content.append(ft.Container(theme.label(month), padding=ft.Padding(4, 12, 0, 0)))
            current_month = month
        content.append(_workout_card(app, w, running=w.id == running_id))
    return content


def _workout_card(app: App, workout: Workout, running: bool) -> ft.Control:
    day = day_label(workout.date, date.today())
    return theme.section(
        ft.Row(
            [
                ft.Column(
                    [
                        theme.label(
                            f"{day} · läuft" if running else day,
                            color=theme.BLUE if running else theme.DIM,
                        ),
                        theme.card_name(
                            workout_title(workout), color=theme.BLUE if running else theme.TEXT
                        ),
                        theme.meta(_summary(app, workout)),
                    ],
                    spacing=6,
                    expand=True,
                ),
                theme.arrow(),
            ]
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
