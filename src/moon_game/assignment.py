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


def can_assign(
    state: GameState,
    rover: Rover,
    order: Order,
    route: Route,
) -> AssignResult:
    if rover not in state.rovers:
        return AssignResult(False, "Rover is not available")
    if order not in state.orders:
        return AssignResult(False, "Order is not available")
    if rover.status is not RoverStatus.IDLE:
        return AssignResult(False, "Rover is busy")
    if rover.position != state.map.base:
        return AssignResult(False, "Rover is not at base")
    if order.status is not OrderStatus.AVAILABLE:
        return AssignResult(False, "Order is not available")
    if order.weight > rover.capacity:
        return AssignResult(False, "Too heavy")
    if not routes_for_order(state, order):
        return AssignResult(False, "No route to that destination")
    if route not in state.routes:
        return AssignResult(False, "Route is not available")
    if route.endpoint != order.endpoint:
        return AssignResult(False, "Route is not for that destination")
    if rover.battery < energy_cost(route, order):
        return AssignResult(False, "Not enough battery")
    return AssignResult(True)


def routes_for_order(state: GameState, order: Order) -> list[Route]:
    return [route for route in state.routes if route.endpoint == order.endpoint]


def energy_cost(route: Route, order: Order) -> float:
    return 2 * route.length * ENERGY_PER_LENGTH + order.weight * ENERGY_PER_WEIGHT
