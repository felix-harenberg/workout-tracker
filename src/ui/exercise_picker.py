from datetime import date

import flet as ft

from core import repository as repo
from core.models import Workout
from core.training import day_label, format_set_compact
from ui import theme
from ui.app import App


def exercise_picker_view(app: App, workout: Workout) -> ft.View:
    route = f"/workout/{workout.id}/add-exercise"
    exercises = repo.list_exercises(app.conn)

    def open_exercise(exercise_id: int) -> None:
        app.go(f"/workout/{workout.id}/exercise/{exercise_id}")

    def add_new(_: ft.Event) -> None:
        try:
            exercise = repo.get_or_create_exercise(app.conn, search.value or "")
        except ValueError:
            app.show_error("Bitte einen Namen eingeben.")
            return
        open_exercise(exercise.id)

    cards: list[ft.Container] = []
    for e in exercises:
        last = repo.last_set_of_exercise(app.conn, e.id)
        subtitle = (
            f"Zuletzt {format_set_compact(last[1])} · {day_label(last[0], date.today())}"
            if last
            else "Noch nie gemacht"
        )
        card = theme.glass_card(
            ft.Row(
                [
                    ft.Column(
                        [theme.name(e.name, size=20), theme.muted(subtitle, size=15)],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.TEXT_MUTED),
                ]
            ),
            on_click=lambda _, eid=e.id: open_exercise(eid),
            padding=14,
        )
        card.data = e.name.casefold()
        cards.append(card)

    new_label = ft.Text("", size=18, color=theme.VIOLET_LIGHT)
    new_card = theme.glass_card(
        ft.Row([ft.Icon(ft.Icons.ADD, color=theme.VIOLET_LIGHT), new_label]),
        on_click=add_new,
        padding=14,
    )
    new_card.visible = False

    def filter_list(_: ft.Event) -> None:
        query = (search.value or "").strip()
        key = query.casefold()
        for card in cards:
            card.visible = key in card.data
        # Offer creating a new exercise unless the name already exists.
        new_card.visible = bool(key) and all(card.data != key for card in cards)
        new_label.value = f"„{query}“ neu anlegen"
        results.update()

    search = theme.text_field(
        hint_text="Übung suchen oder neu anlegen",
        prefix_icon=ft.Icons.SEARCH,
        text_size=18,
        autofocus=not exercises,
        on_change=filter_list,
        on_submit=add_new,
    )
    results = ft.Column([*cards, new_card], spacing=10)

    return theme.view(
        route,
        [theme.headline("Übung ", "wählen", size=52), search, results],
        bar=theme.top_bar(app.back),
        scroll=ft.ScrollMode.AUTO,
    )
