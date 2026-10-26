import pytest

from core.scale import axis_range, nice_step


@pytest.mark.parametrize(
    ("span", "step"), [(15, 5), (42, 20), (8, 2), (10, 2.5), (1, 0.25), (400, 100), (3, 1)]
)
def test_nice_step(span: float, step: float) -> None:
    assert nice_step(span) == step


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [
        (75, 90, (70, 95, 5)),  # values on a step get one step of room
        (81, 89, (80, 90, 2.5)),  # span is at least 10 % of the value: 8.9 / 4 -> 2.5
        (80, 80, (78, 82, 2)),  # a single value still gets a visible range
        (0, 1, (0, 1.25, 0.25)),  # never below zero for positive data
    ],
)
def test_axis_range(low: float, high: float, expected: tuple[float, float, float]) -> None:
    assert axis_range(low, high) == expected


def test_axis_range_bounds_are_multiples_of_step() -> None:
    low, high, step = axis_range(77.5, 102.5)
    assert low % step == 0
    assert high % step == 0
    assert low < 77.5 and high > 102.5
