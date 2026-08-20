from dataclasses import dataclass


@dataclass(frozen=True)
class SelectOrder:
    order_id: str


@dataclass(frozen=True)
class Confirm:
    pass


@dataclass(frozen=True)
class ToggleOrders:
    pass
