from datetime import date

import flet as ft

from core import repository as repo
from core import stats
from core.models import Exercise, Hint, Workout, WorkoutSet
from core.records import check_new_set
from core.templates import copy_missing_sets
from core.training import (
    day_label,
    format_set,
    format_set_compact,
    format_weight,
    hint_message,
    parse_reps,
    parse_weight,
    step_reps,
    step_weight,
    suggest_next_set,
    workout_title,
)
from ui import theme
from ui.app import App
from ui.record_dialogs import show_record, show_suspicious


def exercise_sets_view(app: App, workout: Workout, exercise: Exercise) -> ft.View:
    route = f"/workout/{workout.id}/exercise/{exercise.id}"
    current = [s for s in repo.list_sets(app.conn, workout.id) if s.exercise_id == exercise.id]
    last = repo.last_sets_for_exercise(app.conn, exercise.id, before=workout)
    last_sets = last[1] if last else []

    info: list[ft.Control] = [theme.title_headline(exercise.name, overline=workout_title(workout))]
    hint = repo.get_hint(app.conn, exercise.id)
    # The reminder from last time; it is used up by the first set today.
    if hint and hint.workout_id != workout.id and not current:
        info.append(
            theme.section(
                ft.Row(
                    [
                        theme.hint_glyph(hint.direction, size=22),
                        ft.Text(
                            hint_message(hint, date.today()),
                            size=16,
                            color=theme.TEXT,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                ),
                border_color=theme.hint_color(hint.direction),
                padding=14,
            )
        )
    pr = stats.exercise_pr(app.conn, exercise.id)
    if pr:
        info.append(
            ft.Text(
                f"🏆 PR  {format_set(pr.workout_set)}",
                size=16,
                color=theme.BLUE,
                style=ft.TextStyle(font_family=theme.MONO_FONT),
            )
        )

    def take_missing(_: ft.Event) -> None:
        """Log the sets from last time that are still missing today."""
        copy_missing_sets(app.conn, workout, exercise.id)
        app.render()

    if current or last_sets:
        heading = f"Letztes Mal · {day_label(last[0].date, date.today())}" if last else "Heute"
        info.append(
            theme.section(
                ft.Column(
                    [
                        theme.label(heading),
                        _set_table(app, exercise.name, current, last_sets),
                        *(
                            [
                                ft.Container(
                                    theme.secondary_button(
                                        "Sätze übernehmen", take_missing, ft.Icons.DONE_ALL
                                    ),
                                    padding=ft.Padding(0, 8, 0, 4),
                                )
                            ]
                            if len(last_sets) > len(current)
                            else []
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.Padding(16, 14, 16, 10),
            )
        )
    else:
        info.append(theme.muted("Zum ersten Mal dabei."))

    if current:
        active = hint.direction if hint and hint.workout_id == workout.id else None

        def toggle(direction: Hint) -> None:
            new = None if active == direction else direction
            repo.set_hint(app.conn, exercise.id, workout.id, new)
            app.render()

        info.append(
            ft.Row(
                [
                    theme.label("Nächstes Mal"),
                    ft.Row(
                        [
                            _hint_button(Hint.UP, "Mehr", active == Hint.UP, toggle),
                            _hint_button(Hint.DOWN, "Weniger", active == Hint.DOWN, toggle),
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

    suggestion = suggest_next_set(last_sets, current)
    weight_value, reps_value = suggestion if suggestion else (None, None)
    weight_field = _number_field(
        "kg",
        format_weight(weight_value) if weight_value is not None else "",
        hint="leer = BW",
        # Only right after saving a set: keep the keyboard up, the next set starts at the weight.
        # Other re-renders (e.g. tapping ▲/▼) must not pop up the keyboard.
        autofocus=app.focus_next_set,
    )
    _select_all_now(weight_field)
    app.focus_next_set = False
    reps_field = _number_field("Wdh.", str(reps_value) if reps_value is not None else "")

    async def focus_reps(_: ft.Event) -> None:
        await reps_field.focus()

    def add(_: ft.Event) -> None:
        values = _read_inputs(app, weight_field, reps_field)
        if values is None:
            return
        weight_kg, reps = values
        check = check_new_set(app.conn, exercise.id, weight_kg)

        def save() -> None:
            repo.add_set(app.conn, workout.id, exercise.id, reps=reps, weight_kg=weight_kg)
            app.focus_next_set = True
            app.render()
            if check.is_record:
                show_record(app, exercise.name, weight_kg, reps, check)

        if check.suspicious:

            async def correct() -> None:
                await weight_field.focus()

            show_suspicious(app, exercise.name, weight_kg, reps, check, correct, save)
        else:
            save()

    weight_field.on_submit = focus_reps
    reps_field.on_submit = add

    save_button = ft.Container(
        content=ft.Icon(ft.Icons.CHECK_ROUNDED, color=theme.TEXT, size=34),
        width=68,
        height=64,
        bgcolor=theme.BLUE,
        alignment=ft.Alignment.CENTER,
        tooltip="Satz speichern",
        on_click=add,
        ink=True,
    )

    # Fixed at the bottom, within thumb reach.
    panel = theme.panel(
        ft.Column(
            [
                theme.label(f"Satz {len(current) + 1}", color=theme.BLUE),
                ft.Row([weight_field, reps_field, save_button], spacing=10),
                ft.Row(
                    [
                        _weight_steppers(weight_field),
                        _reps_steppers(reps_field),
                        ft.Container(width=68),
                    ],
                    spacing=10,
                ),
            ],
            spacing=10,
        )
    )

    def delete_exercise(_: ft.Event) -> None:
        app.page.pop_dialog()
        repo.delete_exercise_from_workout(app.conn, workout.id, exercise.id)
        app.go(f"/workout/{workout.id}")

    confirm_delete = theme.dialog(
        "Löschen",
        "Übung entfernen?",
        [
            theme.name_sentence(
                exercise.name, " und alle Sätze davon in diesem Workout werden gelöscht."
            ),
            *(
                [theme.chips([f"{len(current)} {'Satz' if len(current) == 1 else 'Sätze'}"])]
                if current
                else []
            ),
        ],
        [
            ft.Row(
                [
                    theme.dialog_button("Abbrechen", lambda _: app.page.pop_dialog()),
                    theme.dialog_button("Entfernen", delete_exercise, "danger"),
                ],
                spacing=10,
            )
        ],
        danger=True,
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
                theme.icon_button(
                    ft.Icons.DELETE_OUTLINE,
                    lambda _: app.page.show_dialog(confirm_delete),
                    "Übung entfernen",
                )
            ],
        ),
    )


def _set_table(
    app: App, exercise_name: str, current: list[WorkoutSet], last_sets: list[WorkoutSet]
) -> ft.Column:
    """Satz | Vorher | kg | Wdh. Done sets are bright and editable (✎); the ones still to come
    show last time's values faded, like prefilled values in the design."""
    widths = {
        "set": 52,
        "kg": 64,
        "reps": 46,
        "edit": 24,
    }  # "SATZ" with wide letter spacing needs ~50 px

    def cell(text: str, width: int | None, size: int = 18, color: str = theme.TEXT, **kw):
        return ft.Text(
            text,
            width=width,
            size=size,
            color=color,
            style=ft.TextStyle(font_family=theme.MONO_FONT),
            expand=width is None,
            **kw,
        )

    def header(text: str, width: int | None) -> ft.Control:
        return ft.Container(theme.label(text), width=width, expand=width is None)

    rows: list[ft.Control] = [
        ft.Row(
            [
                header("Satz", widths["set"]),
                header("Vorher", None),
                header("kg", widths["kg"]),
                header("Wdh", widths["reps"]),
                ft.Container(width=widths["edit"]),
            ]
        )
    ]
    for i in range(max(len(current), len(last_sets))):
        before = format_set_compact(last_sets[i]) if i < len(last_sets) else "–"
        done = i < len(current)
        shown = current[i] if done else last_sets[i]
        kg = format_weight(shown.weight_kg) if shown.weight_kg is not None else "BW"
        row = ft.Container(
            ft.Row(
                [
                    cell(str(i + 1), widths["set"], color=theme.TEXT_MUTED),
                    cell(before, None, size=15, color=theme.TEXT_MUTED),
                    cell(kg, widths["kg"]),
                    cell(str(shown.reps), widths["reps"]),
                    ft.Container(
                        ft.Icon(ft.Icons.EDIT_OUTLINED, size=18, color=theme.TEXT_MUTED)
                        if done
                        else None,
                        width=widths["edit"],
                    ),
                ]
            ),
            padding=ft.Padding(0, 10, 0, 10),
            border=ft.Border(top=ft.BorderSide(1, theme.LINE)),
            opacity=1 if done else 0.35,
            on_click=(
                lambda _, s=current[i]: app.page.show_dialog(
                    _edit_set_dialog(app, exercise_name, s)
                )
            )
            if done
            else None,
            ink=done,
        )
        rows.append(row)
    return ft.Column(rows, spacing=0)


def _hint_button(direction: Hint, text: str, active: bool, on_toggle) -> ft.Container:
    """Toggle for the next-time reminder; filled when active, tap again to remove."""
    color = theme.hint_color(direction)
    return ft.Container(
        content=ft.Row(
            [
                theme.hint_glyph(direction, size=14),
                ft.Text(text, size=15, color=theme.TEXT if active else theme.TEXT_MUTED),
            ],
            spacing=6,
            tight=True,
        ),
        padding=ft.Padding(12, 8, 14, 8),
        border=ft.Border.all(1, color if active else theme.LINE),
        bgcolor=ft.Colors.with_opacity(0.18, color) if active else None,
        on_click=lambda _: on_toggle(direction),
        ink=True,
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


def _stepper(text: str, field: ft.TextField, change) -> ft.Container:
    """Square ± button that changes `field` with `change` (e.g. step_weight)."""

    def step(_: ft.Event) -> None:
        field.value = change(field.value)
        field.update()

    return ft.Container(
        content=ft.Text(
            text,
            size=15,
            color=theme.TEXT,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(font_family=theme.MONO_FONT),
        ),
        expand=True,
        height=40,
        alignment=ft.Alignment.CENTER,
        border=ft.Border.all(1, theme.LINE),
        on_click=step,
        ink=True,
    )


def _weight_steppers(field: ft.TextField) -> ft.Row:
    return ft.Row(
        [
            _stepper("−2.5", field, lambda v: step_weight(v, -2.5)),
            _stepper("+2.5", field, lambda v: step_weight(v, 2.5)),
        ],
        expand=True,
        spacing=6,
    )


def _reps_steppers(field: ft.TextField) -> ft.Row:
    return ft.Row(
        [
            _stepper("−1", field, lambda v: step_reps(v, -1)),
            _stepper("+1", field, lambda v: step_reps(v, 1)),
        ],
        expand=True,
        spacing=6,
    )


def _edit_set_dialog(app: App, exercise_name: str, workout_set: WorkoutSet) -> ft.AlertDialog:
    """Change or delete a logged set; same fields and ± buttons as the input panel."""
    weight_field = _number_field(
        "kg",
        format_weight(workout_set.weight_kg) if workout_set.weight_kg is not None else "",
        hint="leer = BW",
    )
    reps_field = _number_field("Wdh.", str(workout_set.reps))
    weight_field.expand = reps_field.expand = False  # here they sit in columns, not a row

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

    return theme.dialog(
        f"Satz {workout_set.set_number} · {exercise_name}",
        "Satz bearbeiten",
        [
            ft.Row(
                [
                    ft.Column([weight_field, _weight_steppers(weight_field)], expand=True),
                    ft.Column([reps_field, _reps_steppers(reps_field)], expand=True),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ],
        [
            ft.Row([theme.dialog_button("Speichern", save, "main")]),
            ft.Row(
                [
                    theme.dialog_button("Abbrechen", lambda _: app.page.pop_dialog()),
                    theme.dialog_button("Satz löschen", delete, "danger_outline"),
                ],
                spacing=10,
            ),
        ],
    )


def _select_all_now(field: ft.TextField) -> None:
    """Select the prefilled value: typing replaces it, ✓ keeps it."""
    field.selection = ft.TextSelection(base_offset=0, extent_offset=len(field.value or ""))


def _select_all(e: ft.Event) -> None:
    _select_all_now(e.control)
    e.control.update()
