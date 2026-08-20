from __future__ import annotations

from dataclasses import dataclass

from moon_game.assignment import energy_cost
from moon_game.entities import (
    Delivery,
    DeliveryDirection,
    DeliveryState,
    OrderStatus,
    Rover,
    RoverStatus,
)
from moon_game.game_state import GamePhase, GameState


@dataclass(frozen=True)
class DeliveryCompleted:
    rover: Rover


@dataclass(frozen=True)
class DayEnded:
    pass


type SimEvent = DeliveryCompleted | DayEnded


class Simulation:
    def tick(self, state: GameState, dt: float) -> list[SimEvent]:
        if state.phase is not GamePhase.RUNNING:
            return []
        state.day_elapsed += dt
        if state.day_elapsed >= state.day_length:
            self._abort_active_trips(state)
            return [DayEnded()]
        events: list[SimEvent] = []
        for delivery in state.deliveries:
            if delivery.state is DeliveryState.ACTIVE:
                if self._advance(state, delivery, dt):
                    events.append(DeliveryCompleted(rover=delivery.rover))
        return events

    def _abort_active_trips(self, state: GameState) -> None:
        for delivery in state.deliveries:
            if delivery.state is not DeliveryState.ACTIVE:
                continue
            delivery.rover.status = RoverStatus.IDLE
            delivery.rover.position = state.map.base

    def _advance(self, state: GameState, delivery: Delivery, dt: float) -> bool:
        if delivery.route.length == 0.0:
            self._spend_battery(delivery, 1.0 - delivery.progress)
            self._finish(state, delivery)
            return True
        remaining = 1.0 - delivery.progress
        delta = delivery.rover.speed * dt / delivery.route.length
        applied = min(delta, remaining)
        delivery.progress += applied
        self._spend_battery(delivery, applied)
        if delivery.progress >= 1.0:
            return self._reach_end(state, delivery)
        self._update_position(delivery)
        return False

    def _reach_end(self, state: GameState, delivery: Delivery) -> bool:
        if delivery.direction is DeliveryDirection.TO_DESTINATION:
            delivery.direction = DeliveryDirection.RETURNING
            delivery.progress = 0.0
            delivery.rover.status = RoverStatus.RETURNING
            delivery.rover.position = delivery.route.endpoint.position
            return False
        self._finish(state, delivery)
        return True

    def _finish(self, state: GameState, delivery: Delivery) -> None:
        delivery.progress = 1.0
        delivery.state = DeliveryState.COMPLETED
        delivery.order.status = OrderStatus.COMPLETED
        delivery.rover.status = RoverStatus.IDLE
        delivery.rover.position = delivery.route.start
        delivery.rover.battery = max(0.0, delivery.rover.battery)
        state.money += delivery.order.reward

    def _spend_battery(self, delivery: Delivery, leg_progress: float) -> None:
        cost = energy_cost(delivery.route, delivery.order)
        delivery.rover.battery -= cost * (leg_progress / 2.0)

    def _update_position(self, delivery: Delivery) -> None:
        reverse = delivery.direction is DeliveryDirection.RETURNING
        delivery.rover.position = delivery.route.point_at(
            delivery.progress,
            reverse=reverse,
        )
