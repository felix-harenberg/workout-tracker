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

    rows: list[tuple[str, ft.Control]] = []
    for e in exercises:
        last = repo.last_set_of_exercise(app.conn, e.id)
        text = (
            f"Zuletzt {format_set_compact(last[1])} · {day_label(last[0], date.today())}"
            if last
            else "Noch nie gemacht"
        )
        row = theme.list_row(
            e.name,
            _subtitle(app, e.id, text),
            on_click=lambda _, eid=e.id: open_exercise(eid),
        )
        rows.append((e.name.casefold(), row))

    def build(query: str) -> ft.Control | None:
        """The list for a search: matching exercises, then "„…“ neu anlegen" if it is new."""
        key = query.casefold()
        shown = [row for name, row in rows if key in name]
        if key and all(name != key for name, _ in rows):
            shown.append(
                theme.list_row(
                    f"+ „{query}“ neu anlegen",
                    on_click=add_new,
                    trailing=ft.Container(),
                    color=theme.BLUE,
                )
            )
        return theme.line_list(shown) if shown else None

    def filter_list(_: ft.Event) -> None:
        results.content = build((search.value or "").strip())
        results.update()

    search = theme.text_field(
        hint_text="Suchen oder neu anlegen",
        prefix_icon=ft.Icons.SEARCH,
        autofocus=not exercises,
        on_change=filter_list,
        on_submit=add_new,
    )
    results = ft.Container(build(""))

    return theme.view(
        route,
        [theme.headline("Übung wählen"), search, results],
        bar=theme.top_bar(app.back),
        scroll=ft.ScrollMode.AUTO,
    )


def _subtitle(app: App, exercise_id: int, text: str) -> ft.Control:
    """Last set, with the ▲/▼ reminder in front if one is set."""
    hint = repo.get_hint(app.conn, exercise_id)
    muted = theme.muted(text, size=15)
    if hint is None:
        return muted
    return ft.Row([theme.hint_glyph(hint.direction, size=14), muted], spacing=6)
