"""Frame loop. Simulation.tick() returns SimEvents; Session applies them."""

from moon_game.clock import FrameClock
from moon_game.commands import PlayerCommand
from moon_game.entities import ChooseDelivery
from moon_game.game_state import GamePhase, GameState
from moon_game.simulation import (
    DayEnded,
    DeliveryCompleted,
    HazardStruck,
    SimEvent,
    Simulation,
)
from moon_game.ui import Ui
from moon_game.window_events import WindowEventKind, poll_window_events


class Session:
    def __init__(self, ui: Ui, state: GameState) -> None:
        self._ui = ui
        self._state = state
        self._simulation = Simulation()
        self._clock = FrameClock()

    def run(self) -> None:
        while True:
            dt = self._clock.dt()
            events = poll_window_events()
            if any(event.kind is WindowEventKind.QUIT for event in events):
                break
            commands: list[PlayerCommand] = self._ui.read_commands(events, self._state)
            for command in commands:
                command.apply(self._state)
            if self._should_tick():
                # tick moves the world and returns events that happened this frame
                sim_events = self._simulation.tick(self._state, dt)
                for sim_event in sim_events:
                    self._apply_sim_event(sim_event)
            self._ui.draw(self._state)

    def _should_tick(self) -> bool:
        return self._state.phase is GamePhase.RUNNING and not self._state.paused

    def _apply_sim_event(self, event: SimEvent) -> None:
        if isinstance(event, HazardStruck):
            self._state.hazard_notice = (
                f"{event.rover.name} попал в аварию на маршруте "
                f"{event.route.endpoint.name} {event.route.name}"
            )
            return
        if isinstance(event, DeliveryCompleted):
            self._state.pending_event = ChooseDelivery(rover=event.rover)
            self._state.paused = True
            return
        if isinstance(event, DayEnded):
            self._state.phase = GamePhase.DAY_END
            self._state.pending_event = None
            self._state.hazard_notice = None
