from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from moon_game.entities import (
    Order,
    OrderStatus,
    Route,
    Rover,
    RoverStatus,
)

if TYPE_CHECKING:
    from moon_game.game_state import GameState

ENERGY_PER_LENGTH = 0.05
ENERGY_PER_WEIGHT = 2.0


@dataclass(frozen=True)
class AssignResult:
    allowed: bool
    reason: str = ""


def can_assign(state: GameState, rover: Rover, order: Order) -> AssignResult:
    if rover.status is not RoverStatus.IDLE:
        return AssignResult(False, "Rover is busy")
    if rover.position != state.map.base:
        return AssignResult(False, "Rover is not at base")
    if order.status is not OrderStatus.AVAILABLE:
        return AssignResult(False, "Order is not available")
    route = route_for_order(state, order)
    if route is None:
        return AssignResult(False, "No route to that destination")
    if order.weight > rover.capacity:
        return AssignResult(False, "Too heavy")
    if rover.battery < energy_cost(route, order):
        return AssignResult(False, "Not enough battery")
    return AssignResult(True)


def route_for_order(state: GameState, order: Order) -> Route | None:
    for route in state.routes:
        if route.endpoint == order.endpoint:
            return route
    return None


def energy_cost(route: Route, order: Order) -> float:
    return 2 * route.length * ENERGY_PER_LENGTH + order.weight * ENERGY_PER_WEIGHT
