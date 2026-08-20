from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from moon_game.assignment import can_assign, route_for_order
from moon_game.entities import (
    Delivery,
    Endpoint,
    Map,
    Order,
    OrderStatus,
    Route,
    Rover,
    RoverStatus,
)
from moon_game.geometry import Vec2
from moon_game.world.endpoints import ENDPOINTS
from moon_game.world.orders import build_orders
from moon_game.world.routes import build_routes
from moon_game.world.rovers import build_rovers


class GamePhase(Enum):
    PREP = "prep"
    RUNNING = "running"


@dataclass
class GameState:
    map: Map
    endpoints: list[Endpoint]
    rovers: list[Rover]
    routes: list[Route]
    orders: list[Order]
    deliveries: list[Delivery] = field(default_factory=list)
    money: int = 0
    phase: GamePhase = GamePhase.PREP
    paused: bool = True

    def start_delivery(self, rover: Rover, order: Order) -> None:
        if rover not in self.rovers or order not in self.orders:
            return
        if not can_assign(self, rover, order).allowed:
            return
        route = route_for_order(self, order)
        if route is None:
            return
        rover.status = RoverStatus.EN_ROUTE
        order.status = OrderStatus.IN_PROGRESS
        self.deliveries.append(Delivery(rover=rover, order=order, route=route))

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if not self.paused:
            self.phase = GamePhase.RUNNING


def load_state() -> GameState:
    return initial_state()


def initial_state() -> GameState:
    play_map = Map(id="crater-plain", base=Vec2(120, 400), image_key="map")
    return GameState(
        map=play_map,
        endpoints=list(ENDPOINTS),
        rovers=build_rovers(play_map),
        routes=build_routes(play_map),
        orders=build_orders(),
    )
