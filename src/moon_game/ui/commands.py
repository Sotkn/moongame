from dataclasses import dataclass
from enum import Enum


class OpenPanel(Enum):
    NONE = "none"
    ASSIGNMENT = "assignment"
    SHOP = "shop"


@dataclass(frozen=True)
class SelectOrder:
    order_id: str


@dataclass(frozen=True)
class SelectRover:
    rover_id: str


@dataclass(frozen=True)
class SelectRoute:
    route_id: str


@dataclass(frozen=True)
class Confirm:
    pass


@dataclass(frozen=True)
class ToggleAssign:
    pass


@dataclass(frozen=True)
class ToggleShop:
    pass
