import pytest

from core.run import (
    format_distance,
    format_duration,
    format_pace,
    pace_s_per_km,
    parse_distance,
    parse_duration,
)

# --- parse_duration ---


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        # Digits only, read from the right like a timer: ss, mmss, hmmss
        ("45", 45),
        ("530", 5 * 60 + 30),
        ("4530", 45 * 60 + 30),
        ("23451", 2 * 3600 + 34 * 60 + 51),
        ("100000", 10 * 3600),
        ("9000", 90 * 60),  # 90 minutes without hours is fine
        # With colons
        ("45:30", 45 * 60 + 30),
        ("2:34:51", 2 * 3600 + 34 * 60 + 51),
        ("0:45", 45),
        (" 45:30 ", 45 * 60 + 30),
    ],
)
def test_parse_duration(text: str, seconds: int) -> None:
    assert parse_duration(text) == seconds


@pytest.mark.parametrize(
    "text",
    ["", None, "abc", "0", "00:00", "4575", "45:75", "1:75:00", "1:2:3:4", "-4530", "45.30"],
)
def test_parse_duration_rejects_invalid(text: str | None) -> None:
    with pytest.raises(ValueError):
        parse_duration(text)


# --- format_duration ---


@pytest.mark.parametrize(
    ("seconds", "text"),
    [(45, "0:45"), (330, "5:30"), (2730, "45:30"), (5400, "1:30:00"), (9291, "2:34:51")],
)
def test_format_duration(seconds: int, text: str) -> None:
    assert format_duration(seconds) == text


# --- distance ---


@pytest.mark.parametrize(("text", "km"), [("10", 10.0), ("5,25", 5.25), ("21.1", 21.1)])
def test_parse_distance(text: str, km: float) -> None:
    assert parse_distance(text) == km


@pytest.mark.parametrize("text", ["", None, "0", "-5", "abc"])
def test_parse_distance_rejects_invalid(text: str | None) -> None:
    with pytest.raises(ValueError):
        parse_distance(text)


@pytest.mark.parametrize(("km", "text"), [(10.0, "10 km"), (5.25, "5.25 km"), (21.1, "21.1 km")])
def test_format_distance(km: float, text: str) -> None:
    assert format_distance(km) == text


# --- pace ---


def test_pace_s_per_km() -> None:
    assert pace_s_per_km(distance_km=10, duration_s=50 * 60) == 300


def test_pace_rejects_zero_distance() -> None:
    with pytest.raises(ValueError):
        pace_s_per_km(distance_km=0, duration_s=600)


@pytest.mark.parametrize(
    ("pace", "text"),
    [(300, "5:00 /km"), (323.4, "5:23 /km"), (323.6, "5:24 /km"), (359.6, "6:00 /km")],
)
def test_format_pace_rounds_to_full_seconds(pace: float, text: str) -> None:
    assert format_pace(pace) == text
