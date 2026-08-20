from __future__ import annotations

from moon_game.assignment import energy_cost
from moon_game.entities import (
    Delivery,
    DeliveryDirection,
    DeliveryState,
    OrderStatus,
    RoverStatus,
)
from moon_game.game_state import GameState


class Simulation:
    def tick(self, state: GameState, dt: float) -> None:
        for delivery in state.deliveries:
            if delivery.state is DeliveryState.ACTIVE:
                self._advance(state, delivery, dt)

    def _advance(self, state: GameState, delivery: Delivery, dt: float) -> None:
        if delivery.route.length == 0.0:
            self._spend_battery(delivery, 1.0 - delivery.progress)
            self._finish(state, delivery)
            return
        remaining = 1.0 - delivery.progress
        delta = delivery.rover.speed * dt / delivery.route.length
        applied = min(delta, remaining)
        delivery.progress += applied
        self._spend_battery(delivery, applied)
        if delivery.progress >= 1.0:
            self._reach_end(state, delivery)
            return
        self._update_position(delivery)

    def _reach_end(self, state: GameState, delivery: Delivery) -> None:
        if delivery.direction is DeliveryDirection.TO_DESTINATION:
            delivery.direction = DeliveryDirection.RETURNING
            delivery.progress = 0.0
            delivery.rover.status = RoverStatus.RETURNING
            delivery.rover.position = delivery.route.endpoint.position
            return
        self._finish(state, delivery)

    def _finish(self, state: GameState, delivery: Delivery) -> None:
        delivery.progress = 1.0
        delivery.state = DeliveryState.COMPLETED
        delivery.order.status = OrderStatus.COMPLETED
        delivery.rover.status = RoverStatus.IDLE
        delivery.rover.position = delivery.route.start
        delivery.rover.battery = max(0.0, delivery.rover.battery)
        state.money += delivery.order.reward
        if not any(item.state is DeliveryState.ACTIVE for item in state.deliveries):
            state.paused = True

    def _spend_battery(self, delivery: Delivery, leg_progress: float) -> None:
        cost = energy_cost(delivery.route, delivery.order)
        delivery.rover.battery -= cost * (leg_progress / 2.0)

    def _update_position(self, delivery: Delivery) -> None:
        reverse = delivery.direction is DeliveryDirection.RETURNING
        delivery.rover.position = delivery.route.point_at(
            delivery.progress,
            reverse=reverse,
        )
