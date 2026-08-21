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
    ABORTED = "aborted"


class OrderStatus(Enum):
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class Map:
    id: str
    base: Vec2
    image_key: str


@dataclass
class Rover:
    id: str
    name: str
    position: Vec2
    speed: float
    image_key: str
    capacity: int
    battery: float
    battery_max: float
    status: RoverStatus = RoverStatus.IDLE
    facing: Vec2 = Vec2(1.0, 0.0)


@dataclass(frozen=True)
class ShopOffer:
    id: str
    name: str
    capacity: int
    battery_max: float
    speed: float
    image_key: str
    price: int


@dataclass(frozen=True)
class Endpoint:
    id: str
    name: str
    position: Vec2
    image_key: str


@dataclass
class Order:
    id: str
    name: str
    endpoint: Endpoint
    weight: int
    reward: int
    deadline: float
    status: OrderStatus = OrderStatus.AVAILABLE


@dataclass(frozen=True)
class Route:
    id: str
    name: str
    endpoint: Endpoint
    waypoints: tuple[Vec2, ...]
    length: float
    risk: float

    @staticmethod
    def from_waypoints(
        waypoints: tuple[Vec2, ...],
        *,
        id: str,
        name: str,
        endpoint: Endpoint,
        risk: float,
    ) -> Route:
        path = (*waypoints, endpoint.position)
        length = 0.0
        for start, end in pairwise(path):
            length += start.distance_to(end)
        return Route(
            id=id,
            name=name,
            endpoint=endpoint,
            waypoints=path,
            length=length,
            risk=risk,
        )

    @property
    def start(self) -> Vec2:
        return self.waypoints[0]

    def point_at(self, progress: float, *, reverse: bool = False) -> Vec2:
        start, end, ratio = self._along(progress, reverse=reverse)
        return start.lerp(end, ratio)

    def direction_at(self, progress: float, *, reverse: bool = False) -> Vec2:
        start, end, _ = self._along(progress, reverse=reverse)
        dx = end.x - start.x
        dy = end.y - start.y
        if reverse:
            return Vec2(-dx, -dy)
        return Vec2(dx, dy)

    def _along(
        self, progress: float, *, reverse: bool = False
    ) -> tuple[Vec2, Vec2, float]:
        t = 1.0 - progress if reverse else progress
        t = max(0.0, min(1.0, t))
        origin = self.waypoints[0]
        if self.length == 0.0:
            return origin, origin, 0.0
        remaining = t * self.length
        for start, end in pairwise(self.waypoints):
            segment = start.distance_to(end)
            if remaining <= segment or end is self.waypoints[-1]:
                ratio = remaining / segment if segment > 0.0 else 0.0
                return start, end, ratio
            remaining -= segment
        last = self.waypoints[-1]
        return last, last, 0.0


@dataclass
class Delivery:
    rover: Rover
    order: Order
    route: Route
    progress: float = 0.0
    direction: DeliveryDirection = DeliveryDirection.TO_DESTINATION
    state: DeliveryState = DeliveryState.ACTIVE
    hazard_resolved: bool = False
    stall_remaining: float = 0.0


@dataclass(frozen=True)
class ChooseDelivery:
    rover: Rover
