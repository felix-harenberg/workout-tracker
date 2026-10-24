import flet as ft

from core.models import Run
from core.run import format_duration, parse_distance, parse_duration, run_summary
from ui.app import App


class RunFields:
    """Distance and duration inputs with a live preview of how the input is understood."""

    def __init__(self, app: App, run: Run | None = None) -> None:
        self.app = app
        self.distance = ft.TextField(
            label="Distanz (km)",
            value=f"{run.distance_km:g}" if run else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_change,
            expand=True,
        )
        self.duration = ft.TextField(
            label="Dauer",
            hint_text="4530 = 45:30",
            value=format_duration(run.duration_s) if run else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_change,
            expand=True,
        )
        self.preview = ft.Text(self._preview_text(), color=ft.Colors.GREY)
        self.controls: list[ft.Control] = [ft.Row([self.distance, self.duration]), self.preview]

    def read(self) -> tuple[float, int] | None:
        """Parsed (distance_km, duration_s), or None after showing an error."""
        try:
            distance_km = parse_distance(self.distance.value)
        except ValueError:
            self.app.show_error("Bitte eine gültige Distanz eingeben.")
            return None
        try:
            duration_s = parse_duration(self.duration.value)
        except ValueError:
            self.app.show_error("Ungültige Dauer. Beispiel: 4530 = 45:30, 13000 = 1:30:00")
            return None
        return distance_km, duration_s

    def _preview_text(self) -> str:
        try:
            distance_km = parse_distance(self.distance.value)
        except ValueError:
            distance_km = None
        try:
            duration_s = parse_duration(self.duration.value)
        except ValueError:
            duration_s = None

        if distance_km is not None and duration_s is not None:
            return run_summary(distance_km, duration_s)
        if duration_s is not None:
            return f"Dauer: {format_duration(duration_s)}"
        return ""

    def _on_change(self, _: ft.Event) -> None:
        self.preview.value = self._preview_text()
        self.preview.update()
