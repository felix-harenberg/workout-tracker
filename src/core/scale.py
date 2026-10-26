"""Axis scaling for charts: bounds and label steps on round numbers."""

import math

_NICE_MULTIPLIERS = (1, 2, 2.5, 5, 10)


def nice_step(span: float, max_steps: int = 4) -> float:
    """Smallest round step (1, 2, 2.5 or 5 × 10^k) that covers `span` in `max_steps` steps."""
    raw = span / max_steps
    exponent = math.floor(math.log10(raw))
    for multiplier in _NICE_MULTIPLIERS:
        # Dividing by a power of ten keeps 0.25 exact, multiplying by 0.1 would not.
        step = multiplier * 10**exponent if exponent >= 0 else multiplier / 10**-exponent
        if step >= raw:
            return step
    raise AssertionError("unreachable: 10 × 10^k always covers raw")


def axis_range(low: float, high: float, max_steps: int = 4) -> tuple[float, float, float]:
    """(min, max, step) for an axis showing values from `low` to `high`.

    Bounds are multiples of the step, so chart labels land exactly on them, and
    values never touch the edge. A single value still gets a visible range.
    """
    span = max(high - low, abs(high) * 0.1, 1)
    step = nice_step(span, max_steps)
    axis_min = math.floor(low / step) * step
    axis_max = math.ceil(high / step) * step
    if axis_min == low:
        axis_min -= step
    if axis_max == high:
        axis_max += step
    if low >= 0:
        axis_min = max(axis_min, 0)
    return axis_min, axis_max, step
