"""Domain models. Units: weight in kg."""

from dataclasses import dataclass
from datetime import date


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
