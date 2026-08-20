"""Mutable world state for the current session."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from moon_game.assignment import can_assign, route_for_order
from moon_game.entities import (
    ChooseDelivery,
    Delivery,
    Endpoint,
    Map,
    Order,
    OrderStatus,
    Route,
    Rover,
    RoverStatus,
    ShopOffer,
)
from moon_game.geometry import Vec2
from moon_game.purchase import can_buy
from moon_game.world.day import DAY_LENGTH
from moon_game.world.endpoints import ENDPOINTS
from moon_game.world.orders import build_orders
from moon_game.world.routes import build_routes
from moon_game.world.rovers import build_rovers
from moon_game.world.shop import build_shop_offers


class GamePhase(Enum):
    DAY_START = "day_start"
    RUNNING = "running"
    DAY_END = "day_end"


@dataclass
class GameState:
    map: Map
    endpoints: list[Endpoint]
    rovers: list[Rover]
    routes: list[Route]
    orders: list[Order]
    shop_offers: list[ShopOffer] = field(default_factory=list)
    deliveries: list[Delivery] = field(default_factory=list)
    money: int = 0
    phase: GamePhase = GamePhase.DAY_START
    pending_event: ChooseDelivery | None = None
    paused: bool = True
    day_number: int = 1
    day_elapsed: float = 0.0
    day_length: float = DAY_LENGTH

    def rover_by_id(self, rover_id: str) -> Rover | None:
        for rover in self.rovers:
            if rover.id == rover_id:
                return rover
        return None

    def order_by_id(self, order_id: str) -> Order | None:
        for order in self.orders:
            if order.id == order_id:
                return order
        return None

    def start_delivery(self, rover: Rover, order: Order) -> None:
        if rover not in self.rovers or order not in self.orders:
            return
        if not can_assign(self, rover, order).allowed:
            return
        route = route_for_order(self, order)
        if route is None:
            return
        rover.status = RoverStatus.EN_ROUTE
        order.status = OrderStatus.IN_PROGRESS
        self.deliveries.append(Delivery(rover=rover, order=order, route=route))

    def buy_rover(self, offer: ShopOffer) -> None:
        if not can_buy(self, offer).allowed:
            return
        self.money -= offer.price
        self.shop_offers.remove(offer)
        self.rovers.append(
            Rover(
                id=offer.id,
                position=self.map.base,
                speed=offer.speed,
                image_key=offer.image_key,
                capacity=offer.capacity,
                battery=offer.battery_max,
                battery_max=offer.battery_max,
            )
        )

    def start_next_day(self, orders: list[Order]) -> None:
        self.day_number += 1
        self.orders = orders
        self.deliveries = []
        self.day_elapsed = 0.0
        self.phase = GamePhase.DAY_START
        self.paused = True
        self.pending_event = None
        self._rest_rovers()

    def _rest_rovers(self) -> None:
        for rover in self.rovers:
            rover.status = RoverStatus.IDLE
            rover.position = self.map.base
            rover.battery = rover.battery_max

    def toggle_pause(self) -> None:
        self.paused = not self.paused


def load_state() -> GameState:
    return initial_state()


def initial_state() -> GameState:
    play_map = Map(id="crater-plain", base=Vec2(120, 400), image_key="map")
    return GameState(
        map=play_map,
        endpoints=list(ENDPOINTS),
        rovers=build_rovers(play_map),
        routes=build_routes(play_map),
        orders=build_orders(),
        shop_offers=build_shop_offers(),
        day_length=DAY_LENGTH,
    )


def prepare_next_day(state: GameState) -> None:
    state.start_next_day(build_orders())
