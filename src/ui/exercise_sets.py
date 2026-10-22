import flet as ft

from core import repository as repo
from core.models import Exercise, Workout
from core.training import (
    format_date,
    format_set,
    format_weight,
    parse_reps,
    parse_weight,
    suggest_next_set,
)
from ui.app import App


def exercise_sets_view(app: App, workout: Workout, exercise: Exercise) -> ft.View:
    route = f"/workout/{workout.id}/exercise/{exercise.id}"
    current = [s for s in repo.list_sets(app.conn, workout.id) if s.exercise_id == exercise.id]
    last = repo.last_sets_for_exercise(app.conn, exercise.id, before=workout)
    last_sets = last[1] if last else []

    if last:
        last_workout, sets = last
        history = ft.Text(
            f"Letztes Mal ({format_date(last_workout.date)}):  "
            + "  ·  ".join(format_set(s) for s in sets),
            color=ft.Colors.GREY,
        )
    else:
        history = ft.Text("Zum ersten Mal dabei.", color=ft.Colors.GREY)

    suggestion = suggest_next_set(last_sets, current)
    weight_value, reps_value = suggestion if suggestion else (None, None)
    weight_field = ft.TextField(
        label="kg",
        hint_text="leer = BW",
        value=format_weight(weight_value) if weight_value is not None else "",
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True,
    )
    reps_field = ft.TextField(
        label="Wdh.",
        value=str(reps_value) if reps_value is not None else "",
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True,
    )

    def add(_: ft.Event) -> None:
        try:
            weight_kg = parse_weight(weight_field.value)
        except ValueError:
            app.show_error("Ungültiges Gewicht.")
            return
        try:
            reps = parse_reps(reps_field.value)
        except ValueError:
            app.show_error("Bitte Wiederholungen eingeben.")
            return
        repo.add_set(app.conn, workout.id, exercise.id, reps=reps, weight_kg=weight_kg)
        app.render()

    set_rows: list[ft.Control] = [
        ft.Text(f"Satz {s.set_number}:  {format_set(s)}", size=18) for s in current
    ]

    return ft.View(
        route=route,
        appbar=ft.AppBar(title=ft.Text(exercise.name)),
        controls=[
            history,
            ft.Divider(),
            *set_rows,
            ft.Text(f"Satz {len(current) + 1}", weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    weight_field,
                    reps_field,
                    ft.IconButton(icon=ft.Icons.ADD, tooltip="Satz speichern", on_click=add),
                ]
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )
