"""Small wrappers around flet-charts so the screens stay readable."""

from collections.abc import Callable
from datetime import date

import flet as ft
import flet_charts as fc

CHART_HEIGHT = 220


def _short_date(day: date) -> str:
    return day.strftime("%d.%m.")


def date_line_chart(
    points: list[tuple[date, float]], format_y: Callable[[float], str]
) -> ft.Control:
    """Line chart over time; x is days since the first point so gaps show as gaps."""
    if not points:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    first = points[0][0]
    values = [value for _, value in points]
    low, high = min(values), max(values)
    padding = max((high - low) * 0.15, high * 0.03, 1)
    min_y, max_y = low - padding, high + padding
    last_x = max((points[-1][0] - first).days, 1)

    data = [
        fc.LineChartDataPoint(
            x=(day - first).days,
            y=value,
            tooltip=f"{_short_date(day)}  {format_y(value)}",
        )
        for day, value in points
    ]
    bottom_labels = {0: points[0][0], last_x: points[-1][0]}
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
        left_axis=fc.ChartAxis(
            label_size=48,
            labels=[
                fc.ChartAxisLabel(value=v, label=ft.Text(format_y(v), size=10)) for v in (low, high)
            ],
        ),
        bottom_axis=fc.ChartAxis(
            label_size=24,
            labels=[
                fc.ChartAxisLabel(value=x, label=ft.Text(_short_date(day), size=10))
                for x, day in bottom_labels.items()
            ],
        ),
        horizontal_grid_lines=fc.ChartGridLines(
            interval=(max_y - min_y) / 4, color=ft.Colors.OUTLINE_VARIANT, width=0.5
        ),
        interactive=True,
        height=CHART_HEIGHT,
    )


def week_bar_chart(bars: list[tuple[date, float, str]]) -> ft.Control:
    """Bar chart with one bar per week: (week_start, value, tooltip)."""
    if not bars:
        return ft.Text("Noch keine Daten.", color=ft.Colors.GREY)

    max_value = max(value for _, value, _ in bars) or 1
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
                        tooltip=tooltip,
                    )
                ],
            )
            for i, (_, value, tooltip) in enumerate(bars)
        ],
        max_y=max_value * 1.15,
        left_axis=fc.ChartAxis(
            label_size=32,
            labels=[fc.ChartAxisLabel(value=max_value, label=ft.Text(f"{max_value:g}", size=10))],
        ),
        bottom_axis=fc.ChartAxis(
            label_size=24,
            labels=[
                fc.ChartAxisLabel(value=i, label=ft.Text(_short_date(week), size=10))
                for i, (week, _, _) in enumerate(bars)
                if i % label_every == 0
            ],
        ),
        interactive=True,
        height=CHART_HEIGHT,
    )
