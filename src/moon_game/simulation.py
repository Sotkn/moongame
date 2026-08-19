from __future__ import annotations

from moon_game.entities import Delivery, DeliveryDirection, DeliveryState, RoverStatus
from moon_game.game_state import GamePhase, GameState


class Simulation:
    def tick(self, state: GameState, dt: float) -> None:
        delivery = state.delivery
        if delivery is None or delivery.state is DeliveryState.COMPLETED:
            return
        self._advance(state, delivery, dt)

    def _advance(self, state: GameState, delivery: Delivery, dt: float) -> None:
        if delivery.route.length == 0.0:
            self._finish(state, delivery)
            return
        delivery.progress += delivery.rover.speed * dt / delivery.route.length
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
        delivery.rover.status = RoverStatus.IDLE
        delivery.rover.position = delivery.route.start
        state.phase = GamePhase.PLANNING
        state.paused = False

    def _update_position(self, delivery: Delivery) -> None:
        reverse = delivery.direction is DeliveryDirection.RETURNING
        delivery.rover.position = delivery.route.point_at(
            delivery.progress,
            reverse=reverse,
        )
