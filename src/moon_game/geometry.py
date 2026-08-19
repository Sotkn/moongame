from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def distance_to(self, other: Vec2) -> float:
        dx = other.x - self.x
        dy = other.y - self.y
        return (dx * dx + dy * dy) ** 0.5

    def lerp(self, other: Vec2, t: float) -> Vec2:
        return Vec2(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )

    def to_int_tuple(self) -> tuple[int, int]:
        return (round(self.x), round(self.y))
