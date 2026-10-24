"""Parsing, formatting and pace calculation for runs. Units: km and seconds."""


def parse_duration(text: str | None) -> int:
    """Parse a duration into seconds.

    Digits only are read from the right like a timer: "4530" is 45:30 and
    "23451" is 2:34:51. "45:30" and "2:34:51" work too. Minutes may exceed 59
    only when no hours are given ("9000" is 90 minutes).
    """
    text = (text or "").strip()
    if ":" in text:
        parts = text.split(":")
        if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
            raise ValueError(f"Invalid duration: {text!r}")
        hours, minutes, seconds = ([0] * (3 - len(parts))) + [int(p) for p in parts]
    elif text.isdigit():
        seconds = int(text[-2:])
        minutes = int(text[-4:-2] or 0)
        hours = int(text[:-4] or 0)
    else:
        raise ValueError(f"Invalid duration: {text!r}")

    if seconds >= 60 or (hours and minutes >= 60):
        raise ValueError(f"Invalid duration: {text!r}")
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("Duration must be positive")
    return total


def format_duration(seconds: int) -> str:
    """45 -> "0:45", 2730 -> "45:30", 9291 -> "2:34:51"."""
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def parse_distance(text: str | None) -> float:
    """Parse a distance in km. Accepts "5.25" and "5,25"."""
    distance = float((text or "").strip().replace(",", "."))
    if distance <= 0:
        raise ValueError("Distance must be positive")
    return distance


def format_distance(distance_km: float) -> str:
    return f"{distance_km:g} km"


def pace_s_per_km(distance_km: float, duration_s: int) -> float:
    if distance_km <= 0:
        raise ValueError("Distance must be positive")
    return duration_s / distance_km


def format_pace(pace_s_per_km: float) -> str:
    """300 -> "5:00 /km", rounded to full seconds."""
    minutes, seconds = divmod(round(pace_s_per_km), 60)
    return f"{minutes}:{seconds:02d} /km"
