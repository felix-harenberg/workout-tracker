"""Small wrappers around flet-charts so the screens stay readable."""

import math
from collections.abc import Callable
from datetime import date

import flet as ft
import flet_charts as fc

from core.scale import axis_range, nice_step

CHART_HEIGHT = 220

# Dark tooltip with white text: readable on light and dark themes.
TOOLTIP_BG = ft.Colors.BLUE_GREY_900
TOOLTIP_TEXT = ft.TextStyle(color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.BOLD)


def _short_date(day: date) -> str:
    return day.strftime("%d.%m.")


def _value_axis(axis_min: float, axis_max: float, step: float, fmt: Callable[[float], str]):
    # The chart only asks for labels every `label_spacing`, starting at the axis minimum,
    # so labels must sit exactly on those multiples to be shown.
    count = round((axis_max - axis_min) / step)
    return fc.ChartAxis(
        label_size=48,
        label_spacing=step,
        labels=[
            fc.ChartAxisLabel(
                value=axis_min + i * step, label=ft.Text(fmt(axis_min + i * step), size=10)
            )
            for i in range(count + 1)
        ],
    )


def date_line_chart(
    points: list[tuple[date, float]], format_y: Callable[[float], str]
) -> ft.Control:
    """Line chart over time; x is days since the first point so gaps show as gaps."""
    if not points:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    first = points[0][0]
    values = [value for _, value in points]
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
    return fc.LineChart(
        data_series=[
            fc.LineChartData(
                points=data,
                color=ft.Colors.PRIMARY,
                stroke_width=3,
                curved=True,
                prevent_curve_over_shooting=True,
                point=fc.ChartCirclePoint(radius=4, color=ft.Colors.PRIMARY),
            )
        ],
        min_x=0,
        max_x=last_x,
        min_y=min_y,
        max_y=max_y,
        left_axis=_value_axis(min_y, max_y, step, format_y),
        bottom_axis=fc.ChartAxis(
            label_size=24,
            label_spacing=1,
            labels=[
                fc.ChartAxisLabel(value=0, label=ft.Text(_short_date(first), size=10)),
                fc.ChartAxisLabel(value=last_x, label=ft.Text(_short_date(points[-1][0]), size=10)),
            ],
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            interval=step, color=ft.Colors.OUTLINE_VARIANT, width=0.5
        ),
        tooltip=fc.LineChartTooltip(bgcolor=TOOLTIP_BG),
        interactive=True,
        height=CHART_HEIGHT,
    )


def week_bar_chart(bars: list[tuple[date, float, str]]) -> ft.Control:
    """Bar chart with one bar per week: (week_start, value, tooltip)."""
    if not bars:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    max_value = max(value for _, value, _ in bars) or 1
    step = max(nice_step(max_value), 1)  # counts: no half steps
    max_y = (math.floor(max_value / step) + 1) * step
    label_every = max(len(bars) // 4, 1)
    return fc.BarChart(
        groups=[
            fc.BarChartGroup(
                x=i,
                rods=[
                    fc.BarChartRod(
                        to_y=value,
                        width=14,
                        color=ft.Colors.PRIMARY,
                        border_radius=3,
                        tooltip=fc.BarChartRodTooltip(text=tooltip, text_style=TOOLTIP_TEXT),
                    )
                ],
            )
            for i, (_, value, tooltip) in enumerate(bars)
        ],
        max_y=max_y,
        left_axis=_value_axis(0, max_y, step, lambda v: f"{v:g}"),
        bottom_axis=fc.ChartAxis(
            label_size=24,
            label_spacing=1,
            labels=[
                fc.ChartAxisLabel(value=i, label=ft.Text(_short_date(week), size=10))
                for i, (week, _, _) in enumerate(bars)
                if i % label_every == 0
            ],
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            interval=step, color=ft.Colors.OUTLINE_VARIANT, width=0.5
        ),
        tooltip=fc.BarChartTooltip(bgcolor=TOOLTIP_BG),
        interactive=True,
        height=CHART_HEIGHT,
    )
