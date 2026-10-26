"""Routing: builds the view stack from the current route so Android's back button works."""

import sqlite3

import flet as ft

from core import repository as repo


class App:
    def __init__(self, page: ft.Page, conn: sqlite3.Connection) -> None:
        self.page = page
        self.conn = conn
        self.share = ft.Share()
        # Set right before re-rendering after a saved set, so the next set gets the keyboard.
        self.focus_next_set = False

    def start(self) -> None:
        self.page.on_route_change = lambda _: self.render()
        self.page.on_view_pop = self._on_view_pop
        self.render()

    def go(self, route: str) -> None:
        self.page.navigate(route)

    def show_error(self, message: str) -> None:
        self.page.show_dialog(ft.SnackBar(ft.Text(message)))

    def render(self) -> None:
        # Imported here to avoid a cycle: screens receive the App instance.
        from ui.edit_workout import edit_workout_view
        from ui.exercise_picker import exercise_picker_view
        from ui.exercise_sets import exercise_sets_view
        from ui.exercise_stats import exercise_stats_view
        from ui.new_workout import new_workout_view
        from ui.stats import stats_view
        from ui.workout_detail import workout_detail_view
        from ui.workout_list import workout_list_view

        views = [workout_list_view(self)]
        parts = [p for p in self.page.route.split("/") if p]
        try:
            match parts:
                case ["workout", "new"]:
                    views.append(new_workout_view(self))
                case ["stats"]:
                    views.append(stats_view(self))
                case ["stats", "exercise", exercise_id]:
                    exercise = repo.get_exercise(self.conn, int(exercise_id))
                    if exercise is None:
                        raise LookupError
                    views += [stats_view(self), exercise_stats_view(self, exercise)]
                case ["workout", workout_id, *rest]:
                    workout = repo.get_workout(self.conn, int(workout_id))
                    if workout is None:
                        raise LookupError
                    views.append(workout_detail_view(self, workout))
                    match rest:
                        case ["edit"]:
                            views.append(edit_workout_view(self, workout))
                        case ["add-exercise"]:
                            views.append(exercise_picker_view(self, workout))
                        case ["exercise", exercise_id]:
                            exercise = repo.get_exercise(self.conn, int(exercise_id))
                            if exercise is None:
                                raise LookupError
                            views.append(exercise_sets_view(self, workout, exercise))
        except (ValueError, LookupError):
            views = views[:1]

        self.page.views.clear()
        self.page.views.extend(views)
        self.page.update()

    def back(self, _: ft.Event | None = None) -> None:
        """Go to the screen below; used by the back arrow and Android's back gesture."""
        if len(self.page.views) > 1:
            self.page.views.pop()
            self.go(self.page.views[-1].route)

    def _on_view_pop(self, e: ft.ViewPopEvent) -> None:
        self.back()
