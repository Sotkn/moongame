from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from moon_game.entities import Delivery, Route, Rover, RoverStatus
from moon_game.geometry import Vec2


class GamePhase(Enum):
    PLANNING = "planning"
    EXECUTION = "execution"


@dataclass
class GameState:
    rover: Rover
    route: Route
    phase: GamePhase = GamePhase.PLANNING
    delivery: Delivery | None = None

    def start_delivery(self) -> None:
        if self.phase is not GamePhase.PLANNING:
            return
        self.rover.status = RoverStatus.EN_ROUTE
        self.delivery = Delivery(rover=self.rover, route=self.route)
        self.phase = GamePhase.EXECUTION


def load_state() -> GameState:
    return initial_state()


def initial_state() -> GameState:
    base = Vec2(120, 400)
    route = Route.from_waypoints(
        (
            base,
            Vec2(380, 220),
            Vec2(620, 280),
            Vec2(840, 120),
        )
    )
    rover = Rover(id="rover-1", position=base, speed=140.0)
    return GameState(rover=rover, route=route)
