from datetime import date

import flet as ft

from core import repository as repo
from core import stats
from core.models import Exercise, Workout, WorkoutSet
from core.training import (
    day_label,
    format_set,
    format_set_compact,
    format_weight,
    parse_reps,
    parse_weight,
    suggest_next_set,
)
from ui import theme
from ui.app import App


def exercise_sets_view(app: App, workout: Workout, exercise: Exercise) -> ft.View:
    route = f"/workout/{workout.id}/exercise/{exercise.id}"
    current = [s for s in repo.list_sets(app.conn, workout.id) if s.exercise_id == exercise.id]
    last = repo.last_sets_for_exercise(app.conn, exercise.id, before=workout)
    last_sets = last[1] if last else []

    info: list[ft.Control] = [theme.title_headline(exercise.name)]
    if last:
        last_workout, sets = last
        info.append(
            theme.glass_card(
                ft.Column(
                    [
                        theme.label(f"Letztes Mal · {day_label(last_workout.date, date.today())}"),
                        theme.chips([format_set_compact(s) for s in sets]),
                    ],
                    spacing=10,
                )
            )
        )
    else:
        info.append(theme.muted("Zum ersten Mal dabei."))

    pr = stats.exercise_pr(app.conn, exercise.id)
    if pr:
        info.append(
            ft.Text(
                f"🏆 PR  {format_set(pr.workout_set)}",
                size=17,
                color=theme.VIOLET_LIGHT,
                style=ft.TextStyle(font_family=theme.MEDIUM_FONT),
            )
        )

    if current:
        info.append(ft.Container(theme.label("Heute"), padding=ft.Padding(4, 8, 0, 0)))
    for s in current:
        info.append(
            theme.glass_card(
                ft.Row(
                    [
                        ft.Text(str(s.set_number), size=18, color=theme.TEXT_MUTED, width=28),
                        theme.name(format_set_compact(s), size=24),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.EDIT_OUTLINED, color=theme.TEXT_MUTED, size=20),
                    ]
                ),
                on_click=lambda _, s=s: app.page.show_dialog(_edit_set_dialog(app, s)),
                padding=14,
            )
        )

    suggestion = suggest_next_set(last_sets, current)
    weight_value, reps_value = suggestion if suggestion else (None, None)
    weight_field = _number_field(
        "kg",
        format_weight(weight_value) if weight_value is not None else "",
        hint="leer = BW",
        # After the first set, keep the keyboard up: the next set starts at the weight.
        autofocus=bool(current),
    )
    _select_all_now(weight_field)
    reps_field = _number_field("Wdh.", str(reps_value) if reps_value is not None else "")

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

    # Fixed at the bottom, within thumb reach: the one place with real glass blur.
    panel = theme.glass_panel(
        ft.Column(
            [
                theme.label(f"Satz {len(current) + 1}", color=theme.VIOLET_LIGHT),
                ft.Row(
                    [
                        weight_field,
                        reps_field,
                        ft.IconButton(
                            icon=ft.Icons.CHECK_ROUNDED,
                            tooltip="Satz speichern",
                            bgcolor=theme.VIOLET,
                            icon_color=ft.Colors.WHITE,
                            icon_size=30,
                            on_click=add,
                        ),
                    ],
                    spacing=10,
                ),
            ],
            spacing=8,
        )
    )

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

    return theme.view(
        route,
        [
            ft.Column(
                info,
                spacing=12,
                scroll=ft.ScrollMode.HIDDEN,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            panel,
        ],
        bar=theme.top_bar(
            app.back,
            [
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Übung entfernen",
                    on_click=lambda _: app.page.show_dialog(confirm_delete),
                )
            ],
        ),
    )


def _number_field(
    label: str, value: str, hint: str | None = None, autofocus: bool = False
) -> ft.TextField:
    return theme.text_field(
        label=label,
        hint_text=hint,
        value=value,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_style=ft.TextStyle(font_family=theme.STRONG_FONT, size=24),
        expand=True,
        autofocus=autofocus,
        on_focus=_select_all,
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
    weight_field = _number_field(
        "kg",
        format_weight(workout_set.weight_kg) if workout_set.weight_kg is not None else "",
        hint="leer = BW",
    )
    reps_field = _number_field("Wdh.", str(workout_set.reps))
    weight_field.expand = reps_field.expand = False

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


def _select_all_now(field: ft.TextField) -> None:
    """Select the prefilled value: typing replaces it, ✓ keeps it."""
    field.selection = ft.TextSelection(base_offset=0, extent_offset=len(field.value or ""))


def _select_all(e: ft.Event) -> None:
    _select_all_now(e.control)
    e.control.update()
