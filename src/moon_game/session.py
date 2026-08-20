from moon_game.clock import FrameClock
from moon_game.game_state import GameState
from moon_game.simulation import Simulation
from moon_game.ui import Pause, PlayerCommand, StartDelivery, Ui
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
            commands = self._ui.read_commands(events, self._state)
            self._execute(commands)
            if self._should_tick():
                self._simulation.tick(self._state, dt)
            self._ui.draw(self._state)

    def _execute(self, commands: list[PlayerCommand]) -> None:
        for command in commands:
            self._execute_one(command)

    def _execute_one(self, command: PlayerCommand) -> None:
        if isinstance(command, StartDelivery):
            self._state.start_delivery(command.rover, command.order)
        elif isinstance(command, Pause):
            self._state.toggle_pause()

    def _should_tick(self) -> bool:
        return not self._state.paused
