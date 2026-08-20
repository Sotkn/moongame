from moon_game.clock import FrameClock
from moon_game.commands import PlayerCommand
from moon_game.game_state import GamePhase, GameState
from moon_game.simulation import Simulation
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
                self._simulation.tick(self._state, dt)
            self._ui.draw(self._state)

    def _should_tick(self) -> bool:
        return (
            self._state.phase is GamePhase.RUNNING
            and self._state.pending_event is None
            and not self._state.paused
        )
