from moon_game.clock import FrameClock
from moon_game.game_state import GamePhase, GameState
from moon_game.simulation import Simulation
from moon_game.ui import PlayerCommand, Ui
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
            self._apply(self._ui.read_commands(events))
            if self._should_tick():
                self._simulation.tick(self._state, dt)
            self._ui.draw(self._state)

    def _apply(self, commands: list[PlayerCommand]) -> None:
        if PlayerCommand.START in commands:
            self._state.start_delivery()

    def _should_tick(self) -> bool:
        return self._state.phase is GamePhase.EXECUTION
