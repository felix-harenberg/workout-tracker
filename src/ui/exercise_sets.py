import flet as ft

from core import repository as repo
from core import stats
from core.models import Exercise, Workout, WorkoutSet
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

    pr = stats.exercise_pr(app.conn, exercise.id)
    pr_line: list[ft.Control] = (
        [ft.Text(f"🏆 PR: {stats.format_1rm(pr.best_1rm)} (1RM geschätzt)", color=ft.Colors.GREY)]
        if pr
        else []
    )

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
        # After the first set, keep the keyboard up so the next set is one tap on ✓.
        autofocus=bool(current),
    )

    async def focus_reps(_: ft.Event) -> None:
        await reps_field.focus()

    def add(_: ft.Event) -> None:
        values = _read_inputs(app, weight_field, reps_field)
        if values is None:
            return
        weight_kg, reps = values
        repo.add_set(app.conn, workout.id, exercise.id, reps=reps, weight_kg=weight_kg)
        app.render()

    weight_field.on_submit = focus_reps
    reps_field.on_submit = add

    set_rows: list[ft.Control] = [
        ft.ListTile(
            title=ft.Text(f"Satz {s.set_number}:  {format_set(s)}", size=18),
            trailing=ft.Icon(ft.Icons.EDIT, size=18),
            on_click=lambda _, s=s: app.page.show_dialog(_edit_set_dialog(app, s)),
        )
        for s in current
    ]

    def delete_exercise(_: ft.Event) -> None:
        app.page.pop_dialog()
        repo.delete_exercise_from_workout(app.conn, workout.id, exercise.id)
        app.go(f"/workout/{workout.id}")

    confirm_delete = ft.AlertDialog(
        modal=True,
        title=ft.Text("Übung entfernen?"),
        content=ft.Text(f"Alle Sätze von „{exercise.name}“ in diesem Workout werden gelöscht."),
        actions=[
            ft.TextButton(content="Abbrechen", on_click=lambda _: app.page.pop_dialog()),
            ft.TextButton(content="Löschen", on_click=delete_exercise),
        ],
    )

    return ft.View(
        route=route,
        appbar=ft.AppBar(
            title=ft.Text(exercise.name),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Übung entfernen",
                    on_click=lambda _: app.page.show_dialog(confirm_delete),
                )
            ],
        ),
        controls=[
            history,
            *pr_line,
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


def _read_inputs(
    app: App, weight_field: ft.TextField, reps_field: ft.TextField
) -> tuple[float | None, int] | None:
    """Parse the weight and reps fields, showing an error and returning None if invalid."""
    try:
        weight_kg = parse_weight(weight_field.value)
    except ValueError:
        app.show_error("Ungültiges Gewicht.")
        return None
    try:
        reps = parse_reps(reps_field.value)
    except ValueError:
        app.show_error("Bitte Wiederholungen eingeben.")
        return None
    return weight_kg, reps


def _edit_set_dialog(app: App, workout_set: WorkoutSet) -> ft.AlertDialog:
    weight_field = ft.TextField(
        label="kg",
        hint_text="leer = BW",
        value=format_weight(workout_set.weight_kg) if workout_set.weight_kg is not None else "",
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    reps_field = ft.TextField(
        label="Wdh.", value=str(workout_set.reps), keyboard_type=ft.KeyboardType.NUMBER
    )

    def save(_: ft.Event) -> None:
        values = _read_inputs(app, weight_field, reps_field)
        if values is None:
            return
        weight_kg, reps = values
        repo.update_set(app.conn, workout_set.id, reps=reps, weight_kg=weight_kg)
        app.page.pop_dialog()
        app.render()

    def delete(_: ft.Event) -> None:
        repo.delete_set(app.conn, workout_set.id)
        app.page.pop_dialog()
        app.render()

    return ft.AlertDialog(
        title=ft.Text(f"Satz {workout_set.set_number} bearbeiten"),
        content=ft.Column([weight_field, reps_field], tight=True),
        actions=[
            ft.TextButton(content="Löschen", on_click=delete),
            ft.TextButton(content="Abbrechen", on_click=lambda _: app.page.pop_dialog()),
            ft.TextButton(content="Speichern", on_click=save),
        ],
    )
