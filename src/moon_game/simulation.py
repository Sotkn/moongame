from __future__ import annotations

from dataclasses import dataclass
from random import Random

from moon_game.assignment import energy_cost
from moon_game.entities import (
    Delivery,
    DeliveryDirection,
    DeliveryState,
    OrderStatus,
    Route,
    Rover,
    RoverStatus,
)
from moon_game.game_state import GamePhase, GameState
from moon_game.hazard import (
    HAZARD_AT,
    HAZARD_DELAY,
    HAZARD_ENERGY,
    roll_hazard,
)


@dataclass(frozen=True)
class DeliveryCompleted:
    rover: Rover


@dataclass(frozen=True)
class DayEnded:
    pass


@dataclass(frozen=True)
class HazardStruck:
    rover: Rover
    route: Route


type SimEvent = DeliveryCompleted | DayEnded | HazardStruck


class Simulation:
    """Advances the world each frame. tick() returns SimEvents for Session to apply."""

    def __init__(self, rng: Random | None = None) -> None:
        self._rng = rng if rng is not None else Random()

    def tick(self, state: GameState, dt: float) -> list[SimEvent]:
        if state.phase is not GamePhase.RUNNING:
            return []
        state.day_elapsed += dt
        if state.day_elapsed >= state.day_length:
            state.abort_active_trips()
            return [DayEnded()]
        state.expire_deadlines()
        events: list[SimEvent] = []
        for delivery in state.deliveries:
            if delivery.state is DeliveryState.ACTIVE:
                events.extend(self._advance(state, delivery, dt))
        return events

    def _advance(
        self, state: GameState, delivery: Delivery, dt: float
    ) -> list[SimEvent]:
        if delivery.stall_remaining > 0.0:
            delivery.stall_remaining = max(0.0, delivery.stall_remaining - dt)
            return []
        if delivery.route.length == 0.0:
            delivery.hazard_resolved = True
            self._spend_battery(delivery, 1.0 - delivery.progress)
            self._finish(state, delivery)
            return [DeliveryCompleted(rover=delivery.rover)]
        remaining = 1.0 - delivery.progress
        delta = delivery.rover.speed * dt / delivery.route.length
        applied = min(delta, remaining)
        delivery.progress += applied
        self._spend_battery(delivery, applied)
        events: list[SimEvent] = []
        struck = self._resolve_hazard(delivery)
        if struck is not None:
            events.append(struck)
        if delivery.progress >= 1.0:
            if self._reach_end(state, delivery):
                events.append(DeliveryCompleted(rover=delivery.rover))
            return events
        self._update_position(delivery)
        return events

    def _resolve_hazard(self, delivery: Delivery) -> HazardStruck | None:
        if delivery.hazard_resolved:
            return None
        if delivery.direction is not DeliveryDirection.TO_DESTINATION:
            delivery.hazard_resolved = True
            return None
        if delivery.progress < HAZARD_AT:
            return None
        delivery.hazard_resolved = True
        if not roll_hazard(delivery.route, self._rng):
            return None
        delivery.rover.battery = max(0.0, delivery.rover.battery - HAZARD_ENERGY)
        delivery.stall_remaining = HAZARD_DELAY
        return HazardStruck(rover=delivery.rover, route=delivery.route)

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
        state.completed_count += 1

    def _spend_battery(self, delivery: Delivery, leg_progress: float) -> None:
        cost = energy_cost(delivery.route, delivery.order)
        delivery.rover.battery -= cost * (leg_progress / 2.0)

    def _update_position(self, delivery: Delivery) -> None:
        reverse = delivery.direction is DeliveryDirection.RETURNING
        delivery.rover.position = delivery.route.point_at(
            delivery.progress,
            reverse=reverse,
        )
