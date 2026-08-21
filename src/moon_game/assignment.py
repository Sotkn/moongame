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
        return AssignResult(False, "Ровер недоступен")
    if order not in state.orders:
        return AssignResult(False, "Заказ недоступен")
    if rover.status is not RoverStatus.IDLE:
        return AssignResult(False, "Ровер занят")
    if rover.position != state.map.base:
        return AssignResult(False, "Ровер не на базе")
    if order.status is not OrderStatus.AVAILABLE:
        return AssignResult(False, "Заказ недоступен")
    if order.weight > rover.capacity:
        return AssignResult(False, "Слишком тяжело")
    if not routes_for_order(state, order):
        return AssignResult(False, "Нет маршрута к точке")
    if route not in state.routes:
        return AssignResult(False, "Маршрут недоступен")
    if route.endpoint != order.endpoint:
        return AssignResult(False, "Маршрут не к этой точке")
    if rover.battery < energy_cost(route, order):
        return AssignResult(False, "Не хватает батареи")
    if state.day_elapsed + trip_time(route, rover) > order.deadline:
        return AssignResult(False, "Не успеть к сроку")
    return AssignResult(True)


def routes_for_order(state: GameState, order: Order) -> list[Route]:
    return [route for route in state.routes if route.endpoint == order.endpoint]


def energy_cost(route: Route, order: Order) -> float:
    return 2 * route.length * ENERGY_PER_LENGTH + order.weight * ENERGY_PER_WEIGHT


def trip_time(route: Route, rover: Rover) -> float:
    if route.length == 0.0:
        return 0.0
    return 2 * route.length / rover.speed
