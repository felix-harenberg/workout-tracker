"""Small wrappers around flet-charts so the screens stay readable."""

import math
from collections.abc import Callable
from datetime import date

import flet as ft
import flet_charts as fc

from core.scale import axis_range, nice_step
from ui.theme import BG, BLUE, MONO_FONT, TEXT, TEXT_MUTED

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

    Tap a bar and its tooltip stays; tap it again (or next to the bars) and it goes away.
    The chart's own touch handling is off for that: with `interactive=False`, a rod's
    `selected` keeps its tooltip on screen, and the tap event switches it.
    """
    if not bars:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    max_value = max(value for _, value, _ in bars) or 1
    step = max(nice_step(max_value), 1)  # counts: no half steps
    max_y = (math.floor(max_value / step) + 1) * step
    label_every = max(len(bars) // 4, 1)
    rods = [
        fc.BarChartRod(
            to_y=value,
            width=14,
            color=BLUE,
            border_radius=0,
            tooltip=fc.BarChartRodTooltip(text=tooltip, text_style=TOOLTIP_TEXT),
        )
        for _, value, tooltip in bars
    ]

    def toggle_tooltip(e: fc.BarChartEvent) -> None:
        if e.type != fc.ChartEventType.TAP_UP:
            return
        for i, rod in enumerate(rods):
            rod.selected = i == e.group_index and not rod.selected
        chart.update()

    chart = fc.BarChart(
        groups=[fc.BarChartGroup(x=i, rods=[rod]) for i, rod in enumerate(rods)],
        on_event=toggle_tooltip,
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
        tooltip=fc.BarChartTooltip(bgcolor=TOOLTIP_BG, border_side=TOOLTIP_BORDER, border_radius=0),
        interactive=False,
        height=CHART_HEIGHT,
    )
    return chart
