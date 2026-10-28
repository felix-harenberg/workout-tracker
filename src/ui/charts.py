"""Small wrappers around flet-charts so the screens stay readable."""

import math
from collections.abc import Callable
from datetime import date

import flet as ft
import flet_charts as fc

from core.scale import axis_range, nice_step
from ui.theme import BG, BLUE, DIM, MONO_FONT, TEXT, TEXT_MUTED

CHART_HEIGHT = 220

# Tooltip in the app's look: black box, blue frame, square corners, white mono text.
TOOLTIP_BG = BG
TOOLTIP_BORDER = ft.BorderSide(1, BLUE)
TOOLTIP_TEXT = ft.TextStyle(color=TEXT, size=13, font_family=MONO_FONT, height=1.4)


def _short_date(day: date) -> str:
    return day.strftime("%d.%m.")


def _value_axis(
    axis_min: float,
    axis_max: float,
    step: float,
    fmt: Callable[[float], str],
    skip_min: bool = False,
):
    # The chart only asks for labels every `label_spacing`, starting at the axis minimum,
    # so labels must sit exactly on those multiples to be shown.
    # `skip_min` leaves out the lowest label, which would collide with the first date.
    count = round((axis_max - axis_min) / step)
    return fc.ChartAxis(
        label_size=48,
        label_spacing=step,
        show_min=not skip_min,  # otherwise the chart adds its own label at the minimum
        labels=[
            fc.ChartAxisLabel(
                value=axis_min + i * step,
                label=ft.Text(fmt(axis_min + i * step), size=12, color=TEXT_MUTED),
            )
            for i in range(1 if skip_min else 0, count + 1)
        ],
    )


def date_line_chart(
    points: list[tuple[date, float]],
    format_y: Callable[[float], str],
    goal: float | None = None,
    color: str = ft.Colors.PRIMARY,
) -> ft.Control:
    """Line chart over time; x is days since the first point so gaps show as gaps.

    With `goal`, a dashed blue line marks it; the axis includes it, so it never sits
    on the edge of the chart.
    """
    if not points:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    first = points[0][0]
    values = [value for _, value in points] + ([goal] if goal is not None else [])
    min_y, max_y, step = axis_range(min(values), max(values))
    last_x = max((points[-1][0] - first).days, 1)

    data = [
        fc.LineChartDataPoint(
            x=(day - first).days,
            y=value,
            tooltip=fc.LineChartDataPointTooltip(
                text=f"{_short_date(day)}  {format_y(value)}", text_style=TOOLTIP_TEXT
            ),
        )
        for day, value in points
    ]
    series = [
        fc.LineChartData(
            points=data,
            color=color,
            stroke_width=3,
            # Straight segments: a curve would suggest values between trainings.
            curved=False,
            point=fc.ChartCirclePoint(radius=4, color=color),
        )
    ]
    if goal is not None:
        series.append(
            fc.LineChartData(
                points=[
                    fc.LineChartDataPoint(x=0, y=goal, show_tooltip=False),
                    fc.LineChartDataPoint(x=last_x, y=goal, show_tooltip=False),
                ],
                color=BLUE,
                stroke_width=2,
                dash_pattern=[8, 6],
                point=False,
            )
        )
    chart = fc.LineChart(
        data_series=series,
        min_x=0,
        max_x=last_x,
        min_y=min_y,
        max_y=max_y,
        left_axis=_value_axis(min_y, max_y, step, format_y, skip_min=True),
        bottom_axis=fc.ChartAxis(
            label_size=24,
            label_spacing=1,
            labels=[
                fc.ChartAxisLabel(
                    value=0, label=ft.Text(_short_date(first), size=12, color=TEXT_MUTED)
                ),
                fc.ChartAxisLabel(
                    value=last_x,
                    label=ft.Text(_short_date(points[-1][0]), size=12, color=TEXT_MUTED),
                ),
            ],
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            interval=step, color=ft.Colors.OUTLINE_VARIANT, width=0.5
        ),
        tooltip=fc.LineChartTooltip(
            bgcolor=TOOLTIP_BG, border_side=TOOLTIP_BORDER, border_radius=0
        ),
        interactive=True,
        height=CHART_HEIGHT,
    )
    # Room on the right so the last date label is not cut off.
    return ft.Container(chart, padding=ft.Padding(0, 0, 16, 0))


def week_bar_chart(bars: list[tuple[date, float, str]]) -> ft.Control:
    """Bar chart with one bar per week: (week_start, value, tooltip).

    Tap a bar and its details stay in a box above the chart, with the bar highlighted;
    tap it again (or next to the bars) and they go away. The chart's own tooltip only
    shows while the finger is down, and with `interactive=False` flet_charts sends no
    taps at all, so the pinned tooltip is our own box and the chart only reports taps.
    """
    if not bars:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    max_value = max(value for _, value, _ in bars) or 1
    step = max(nice_step(max_value), 1)  # counts: no half steps
    max_y = (math.floor(max_value / step) + 1) * step
    label_every = max(len(bars) // 4, 1)
    rods = [
        fc.BarChartRod(to_y=value, width=14, color=BLUE, border_radius=0, show_tooltip=False)
        for _, value, _ in bars
    ]
    info_text = ft.Text("", style=TOOLTIP_TEXT)
    info = ft.Container(info_text, padding=ft.Padding(12, 6, 12, 6))
    selected: int | None = None

    def show(index: int | None) -> None:
        nonlocal selected
        selected = index
        for i, rod in enumerate(rods):
            rod.color = BLUE if index in (None, i) else ft.Colors.with_opacity(0.3, BLUE)
        if index is None:
            info_text.value = "Tippe auf einen Balken"
            info_text.color = DIM
            info.bgcolor, info.border = None, None
        else:
            info_text.value = bars[index][2].replace("\n", " · ")
            info_text.color = TEXT
            info.bgcolor, info.border = TOOLTIP_BG, ft.Border.all(1, BLUE)

    def on_tap(e: fc.BarChartEvent) -> None:
        if e.type != fc.ChartEventType.TAP_UP:
            return
        show(None if e.group_index is None or e.group_index == selected else e.group_index)
        box.update()

    chart = fc.BarChart(
        groups=[fc.BarChartGroup(x=i, rods=[rod]) for i, rod in enumerate(rods)],
        on_event=on_tap,
        max_y=max_y,
        left_axis=_value_axis(0, max_y, step, lambda v: f"{v:g}"),
        bottom_axis=fc.ChartAxis(
            label_size=24,
            label_spacing=1,
            labels=[
                fc.ChartAxisLabel(
                    value=i, label=ft.Text(_short_date(week), size=12, color=TEXT_MUTED)
                )
                for i, (week, _, _) in enumerate(bars)
                if i % label_every == 0
            ],
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            interval=step, color=ft.Colors.OUTLINE_VARIANT, width=0.5
        ),
        interactive=True,  # needed for taps to arrive at all
        height=CHART_HEIGHT,
    )
    show(None)
    # Fixed height above the chart, so the chart does not jump when the box appears.
    box = ft.Column([ft.Container(ft.Row([info]), height=40), chart], spacing=8)
    return box
