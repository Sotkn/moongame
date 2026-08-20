from dataclasses import dataclass

from moon_game.entities import Order


@dataclass(frozen=True)
class SelectOrder:
    order: Order


@dataclass(frozen=True)
class Confirm:
    pass
