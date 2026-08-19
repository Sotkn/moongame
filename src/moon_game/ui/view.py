from __future__ import annotations

from collections.abc import Sequence

import pygame

from moon_game.game_state import GamePhase, GameState
from moon_game.ui.commands import PlayerCommand
from moon_game.window_events import WindowEvent, WindowEventKind

WINDOW_SIZE = (960, 540)
BACKGROUND = (28, 30, 38)
ROUTE_COLOR = (92, 98, 112)
BASE_COLOR = (196, 202, 214)
DESTINATION_COLOR = (220, 168, 72)
ROVER_COLOR = (110, 196, 154)
BUTTON_IDLE = (70, 92, 122)
BUTTON_DISABLED = (48, 54, 64)
BUTTON_TEXT = (236, 238, 242)
LABEL_COLOR = (168, 174, 186)

START_BUTTON = pygame.Rect(400, 480, 160, 40)


class Ui:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Moon Courier Crisis")
        self._screen = pygame.display.set_mode(WINDOW_SIZE)
        self._font = pygame.font.SysFont("segoe ui", 18)

    def read_commands(self, events: Sequence[WindowEvent]) -> list[PlayerCommand]:
        commands: list[PlayerCommand] = []
        for event in events:
            if event.kind is WindowEventKind.CLICK and event.position is not None:
                if START_BUTTON.collidepoint(event.position):
                    commands.append(PlayerCommand.START)
        return commands

    def draw(self, state: GameState) -> None:
        self._draw_map(state)
        self._draw_button(state.phase is GamePhase.PLANNING)
        status = self._font.render(
            state.rover.status.value.replace("_", " "),
            True,
            LABEL_COLOR,
        )
        self._screen.blit(status, (24, 20))
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()

    def _draw_map(self, state: GameState) -> None:
        self._screen.fill(BACKGROUND)
        points = [point.to_int_tuple() for point in state.route.waypoints]
        pygame.draw.lines(self._screen, ROUTE_COLOR, False, points, 3)
        pygame.draw.circle(
            self._screen,
            BASE_COLOR,
            state.route.start.to_int_tuple(),
            14,
        )
        pygame.draw.circle(
            self._screen,
            DESTINATION_COLOR,
            state.route.destination.to_int_tuple(),
            12,
        )
        pygame.draw.circle(
            self._screen,
            ROVER_COLOR,
            state.rover.position.to_int_tuple(),
            10,
        )
        self._draw_label("Base", state.route.start.to_int_tuple(), (0, 22))
        self._draw_label(
            "Destination",
            state.route.destination.to_int_tuple(),
            (0, -28),
        )

    def _draw_label(
        self,
        text: str,
        origin: tuple[int, int],
        offset: tuple[int, int],
    ) -> None:
        surface = self._font.render(text, True, LABEL_COLOR)
        rect = surface.get_rect(
            center=(origin[0] + offset[0], origin[1] + offset[1]),
        )
        self._screen.blit(surface, rect)

    def _draw_button(self, enabled: bool) -> None:
        color = BUTTON_IDLE if enabled else BUTTON_DISABLED
        pygame.draw.rect(self._screen, color, START_BUTTON, border_radius=6)
        label = self._font.render("Start", True, BUTTON_TEXT)
        self._screen.blit(label, label.get_rect(center=START_BUTTON.center))
