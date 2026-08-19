from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import pairwise

from moon_game.geometry import Vec2


class RoverStatus(Enum):
    IDLE = "idle"
    EN_ROUTE = "en_route"
    RETURNING = "returning"


class DeliveryDirection(Enum):
    TO_DESTINATION = "to_destination"
    RETURNING = "returning"


class DeliveryState(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class Rover:
    id: str
    position: Vec2
    speed: float
    status: RoverStatus = RoverStatus.IDLE


@dataclass(frozen=True)
class Route:
    waypoints: tuple[Vec2, ...]
    length: float

    @staticmethod
    def from_waypoints(waypoints: tuple[Vec2, ...]) -> Route:
        length = 0.0
        for start, end in pairwise(waypoints):
            length += start.distance_to(end)
        return Route(waypoints=waypoints, length=length)

    @property
    def start(self) -> Vec2:
        return self.waypoints[0]

    @property
    def destination(self) -> Vec2:
        return self.waypoints[-1]

    def point_at(self, progress: float, *, reverse: bool = False) -> Vec2:
        t = 1.0 - progress if reverse else progress
        t = max(0.0, min(1.0, t))
        if self.length == 0.0:
            return self.waypoints[0]
        target = t * self.length
        remaining = target
        for start, end in pairwise(self.waypoints):
            segment = start.distance_to(end)
            if remaining <= segment or end is self.waypoints[-1]:
                ratio = remaining / segment if segment > 0.0 else 0.0
                return start.lerp(end, ratio)
            remaining -= segment
        return self.waypoints[-1]


@dataclass
class Delivery:
    rover: Rover
    route: Route
    progress: float = 0.0
    direction: DeliveryDirection = DeliveryDirection.TO_DESTINATION
    state: DeliveryState = DeliveryState.ACTIVE
