from __future__ import annotations

from collections.abc import Sequence

import pygame

from moon_game.asset_catalog import asset_path
from moon_game.entities import Endpoint, Route, Rover
from moon_game.game_state import GameState
from moon_game.ui.buttons import Button, build_buttons, button_enabled
from moon_game.ui.commands import PlayerCommand
from moon_game.window_events import WindowEvent, WindowEventKind

WINDOW_SIZE = (960, 540)
ROUTE_COLOR = (92, 98, 112)
BASE_COLOR = (196, 202, 214)
DESTINATION_COLOR = (220, 168, 72)
BUTTON_IDLE = (70, 92, 122)
BUTTON_DISABLED = (48, 54, 64)
BUTTON_TEXT = (236, 238, 242)
LABEL_COLOR = (168, 174, 186)


class Ui:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Moon Courier Crisis")
        self._screen = pygame.display.set_mode(WINDOW_SIZE)
        self._font = pygame.font.SysFont("segoe ui", 18)
        self._images: dict[str, pygame.Surface] = {}

    def read_commands(
        self,
        events: Sequence[WindowEvent],
        state: GameState,
    ) -> list[PlayerCommand]:
        buttons = build_buttons(state, WINDOW_SIZE)
        commands: list[PlayerCommand] = []
        for event in events:
            command = self._command_from_click(event, buttons, state)
            if command is not None:
                commands.append(command)
        return commands

    def draw(self, state: GameState) -> None:
        self._draw_map(state)
        self._draw_rover(state.rovers[0])
        self._draw_buttons(state)
        self._draw_status(state.rovers[0])
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()

    def _command_from_click(
        self,
        event: WindowEvent,
        buttons: Sequence[Button],
        state: GameState,
    ) -> PlayerCommand | None:
        if event.kind is not WindowEventKind.CLICK or event.position is None:
            return None
        for button in buttons:
            if not button.rect.collidepoint(event.position):
                continue
            if button_enabled(button, state):
                return button.command
        return None

    def _draw_map(self, state: GameState) -> None:
        self._screen.blit(self._image(state.map.image_key), (0, 0))
        for route in state.routes:
            self._draw_route(route)
        for endpoint in state.endpoints:
            self._draw_endpoint(endpoint)
        pygame.draw.circle(
            self._screen,
            BASE_COLOR,
            state.map.base.to_int_tuple(),
            14,
        )
        self._draw_label("Base", state.map.base.to_int_tuple(), (0, 22))

    def _draw_route(self, route: Route) -> None:
        points = [point.to_int_tuple() for point in route.waypoints]
        pygame.draw.lines(self._screen, ROUTE_COLOR, False, points, 3)

    def _draw_endpoint(self, endpoint: Endpoint) -> None:
        pygame.draw.circle(
            self._screen,
            DESTINATION_COLOR,
            endpoint.position.to_int_tuple(),
            12,
        )
        self._draw_label(endpoint.name, endpoint.position.to_int_tuple(), (0, -28))

    def _draw_rover(self, rover: Rover) -> None:
        image = self._image(rover.image_key)
        rect = image.get_rect(center=rover.position.to_int_tuple())
        self._screen.blit(image, rect)

    def _draw_buttons(self, state: GameState) -> None:
        for button in build_buttons(state, WINDOW_SIZE):
            enabled = button_enabled(button, state)
            color = BUTTON_IDLE if enabled else BUTTON_DISABLED
            pygame.draw.rect(self._screen, color, button.rect, border_radius=6)
            label = self._font.render(button.label, True, BUTTON_TEXT)
            self._screen.blit(label, label.get_rect(center=button.rect.center))

    def _draw_status(self, rover: Rover) -> None:
        status = self._font.render(
            rover.status.value.replace("_", " "),
            True,
            LABEL_COLOR,
        )
        self._screen.blit(status, (24, 20))

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

    def _image(self, key: str) -> pygame.Surface:
        loaded = self._images.get(key)
        if loaded is None:
            loaded = pygame.image.load(asset_path(key)).convert_alpha()
            self._images[key] = loaded
        return loaded
