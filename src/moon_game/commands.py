from __future__ import annotations

from dataclasses import dataclass

from moon_game.entities import ChooseDelivery, Order, Route, Rover, ShopOffer
from moon_game.game_state import GamePhase, GameState, prepare_next_day


@dataclass(frozen=True)
class StartDelivery:
    rover: Rover
    order: Order
    route: Route

    def apply(self, state: GameState) -> None:
        if state.phase not in (GamePhase.DAY_START, GamePhase.RUNNING):
            return
        before = len(state.deliveries)
        state.start_delivery(self.rover, self.order, self.route)
        if len(state.deliveries) == before:
            return
        if isinstance(state.pending_event, ChooseDelivery):
            state.pending_event = None
        state.paused = False


@dataclass(frozen=True)
class StartDay:
    def apply(self, state: GameState) -> None:
        if state.phase is not GamePhase.DAY_START:
            return
        state.phase = GamePhase.RUNNING
        state.paused = False


@dataclass(frozen=True)
class DismissChoice:
    def apply(self, state: GameState) -> None:
        if not isinstance(state.pending_event, ChooseDelivery):
            return
        state.pending_event = None
        if state.phase is GamePhase.RUNNING:
            state.paused = False


@dataclass(frozen=True)
class Pause:
    def apply(self, state: GameState) -> None:
        if state.phase is GamePhase.RUNNING:
            state.toggle_pause()


@dataclass(frozen=True)
class NextDay:
    def apply(self, state: GameState) -> None:
        if state.phase is not GamePhase.DAY_END:
            return
        if state.is_final_day():
            return
        prepare_next_day(state)


@dataclass(frozen=True)
class BuyRover:
    offer: ShopOffer

    def apply(self, state: GameState) -> None:
        if state.phase not in (GamePhase.DAY_START, GamePhase.RUNNING):
            return
        state.buy_rover(self.offer)


@dataclass(frozen=True)
class EndDay:
    def apply(self, state: GameState) -> None:
        if state.phase not in (GamePhase.DAY_START, GamePhase.RUNNING):
            return
        state.abort_active_trips()
        state.day_elapsed = state.day_length
        state.phase = GamePhase.DAY_END
        state.pending_event = None
        state.hazard_notice = None


type PlayerCommand = (
    StartDelivery | StartDay | DismissChoice | Pause | NextDay | BuyRover | EndDay
)
