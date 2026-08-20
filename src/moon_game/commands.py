from __future__ import annotations

from dataclasses import dataclass

from moon_game.entities import ChooseDelivery, DeliveryState, Order, Rover
from moon_game.game_state import GamePhase, GameState


@dataclass(frozen=True)
class StartDelivery:
    rover: Rover
    order: Order

    def apply(self, state: GameState) -> None:
        state.start_delivery(self.rover, self.order)


@dataclass(frozen=True)
class StartDay:
    def apply(self, state: GameState) -> None:
        if state.phase is not GamePhase.DAY_START:
            return
        if not _has_active_delivery(state):
            return
        state.phase = GamePhase.RUNNING
        state.paused = False


@dataclass(frozen=True)
class ResumeFromChoice:
    def apply(self, state: GameState) -> None:
        if not isinstance(state.pending_event, ChooseDelivery):
            return
        if not _has_active_delivery(state):
            return
        state.pending_event = None
        state.paused = False


@dataclass(frozen=True)
class DismissChoice:
    def apply(self, state: GameState) -> None:
        state.pending_event = None
        state.paused = True


@dataclass(frozen=True)
class Pause:
    def apply(self, state: GameState) -> None:
        if state.phase is GamePhase.RUNNING and state.pending_event is None:
            state.toggle_pause()


type PlayerCommand = StartDelivery | StartDay | ResumeFromChoice | DismissChoice | Pause


def _has_active_delivery(state: GameState) -> bool:
    return any(item.state is DeliveryState.ACTIVE for item in state.deliveries)
