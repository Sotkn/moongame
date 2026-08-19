from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from moon_game.entities import Delivery, Endpoint, Map, Route, Rover, RoverStatus
from moon_game.geometry import Vec2
from moon_game.world.endpoints import ENDPOINTS
from moon_game.world.routes import build_routes
from moon_game.world.rovers import build_rovers


class GamePhase(Enum):
    PLANNING = "planning"
    EXECUTION = "execution"


@dataclass
class GameState:
    map: Map
    endpoints: list[Endpoint]
    rovers: list[Rover]
    routes: list[Route]
    delivery: Delivery | None = None
    phase: GamePhase = GamePhase.PLANNING
    paused: bool = False

    def start_delivery(self, route: Route) -> None:
        if route not in self.routes:
            return
        rover = self._idle_rover()
        if rover is None:
            return
        rover.status = RoverStatus.EN_ROUTE
        self.delivery = Delivery(rover=rover, route=route)
        self.phase = GamePhase.EXECUTION

    def toggle_pause(self) -> None:
        if self.phase is not GamePhase.EXECUTION:
            return
        self.paused = not self.paused

    def _idle_rover(self) -> Rover | None:
        for rover in self.rovers:
            if rover.status is RoverStatus.IDLE:
                return rover
        return None


def load_state() -> GameState:
    return initial_state()


def initial_state() -> GameState:
    play_map = Map(id="crater-plain", base=Vec2(120, 400), image_key="map")
    return GameState(
        map=play_map,
        endpoints=list(ENDPOINTS),
        rovers=build_rovers(play_map),
        routes=build_routes(play_map),
    )
