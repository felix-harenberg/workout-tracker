"""Domain models. Units: weight and distance in kg and km, durations in seconds."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class WorkoutType(StrEnum):
    STRENGTH = "strength"
    RUN = "run"


class Hint(StrEnum):
    """Reminder for next time: go up or down in weight."""

    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class Exercise:
    id: int
    name: str


@dataclass(frozen=True)
class Workout:
    id: int
    name: str
    date: date
    notes: str = ""
    type: WorkoutType = WorkoutType.STRENGTH


@dataclass(frozen=True)
class WorkoutSet:
    id: int
    workout_id: int
    exercise_id: int
    set_number: int
    reps: int
    weight_kg: float | None = None

    @property
    def is_bodyweight(self) -> bool:
        return self.weight_kg is None


@dataclass(frozen=True)
class Run:
    workout_id: int
    distance_km: float
    duration_s: int


@dataclass(frozen=True)
class WeightHint:
    direction: Hint
    workout_id: int | None  # where it was set; None if that workout was deleted
    set_on: date | None
