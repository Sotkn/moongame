from dataclasses import dataclass

from moon_game.entities import Order, Rover


@dataclass(frozen=True)
class SelectOrder:
    order: Order


@dataclass(frozen=True)
class SelectRover:
    rover: Rover


@dataclass(frozen=True)
class Confirm:
    pass


@dataclass(frozen=True)
class StartDelivery:
    rover: Rover
    order: Order


@dataclass(frozen=True)
class Pause:
    pass


type PlayerCommand = StartDelivery | Pause
