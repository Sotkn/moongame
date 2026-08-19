from dataclasses import dataclass

from moon_game.entities import Route


@dataclass(frozen=True)
class StartRoute:
    route: Route


@dataclass(frozen=True)
class Pause:
    pass


type PlayerCommand = StartRoute | Pause
