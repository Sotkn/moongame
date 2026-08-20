from __future__ import annotations

from collections.abc import Sequence

import pygame

from moon_game.asset_catalog import asset_path
from moon_game.entities import Endpoint, Order, Route, Rover
from moon_game.game_state import GameState
from moon_game.ui.buttons import (
    Button,
    build_buttons,
    button_enabled,
    button_selected,
    confirm_reason,
)
from moon_game.ui.commands import (
    Confirm,
    Pause,
    PlayerCommand,
    SelectOrder,
    SelectRover,
    StartDelivery,
)
from moon_game.window_events import WindowEvent, WindowEventKind

WINDOW_SIZE = (960, 540)
ROUTE_COLOR = (92, 98, 112)
BUTTON_IDLE = (70, 92, 122)
BUTTON_SELECTED = (110, 150, 190)
BUTTON_DISABLED = (48, 54, 64)
BUTTON_TEXT = (236, 238, 242)
LABEL_COLOR = (168, 174, 186)
REASON_COLOR = (220, 140, 96)
BATTERY_BACK = (42, 46, 54)
BATTERY_FILL = (88, 176, 124)
SPRITE_MAX_SIZE = {
    "rover": 48,
    "base": 100,
    "poi1": 70,
    "poi2": 70,
    "poi3": 70,
}


class Ui:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Moon Courier Crisis")
        self._screen = pygame.display.set_mode(WINDOW_SIZE)
        self._font = pygame.font.SysFont("segoe ui", 18)
        self._images: dict[str, pygame.Surface] = {}
        self._selected_order: Order | None = None
        self._selected_rover: Rover | None = None

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
        for rover in state.rovers:
            self._draw_rover(rover)
        self._draw_buttons(state)
        self._draw_hud(state)
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
            if not button_enabled(
                button,
                state,
                self._selected_order,
                self._selected_rover,
            ):
                continue
            return self._command_from_button(button)
        return None

    def _command_from_button(self, button: Button) -> PlayerCommand | None:
        command = button.command
        if isinstance(command, SelectOrder):
            self._selected_order = command.order
            return None
        if isinstance(command, SelectRover):
            self._selected_rover = command.rover
            return None
        if isinstance(command, Confirm):
            order = self._selected_order
            rover = self._selected_rover
            if order is None or rover is None:
                return None
            return StartDelivery(rover, order)
        if isinstance(command, Pause):
            return command
        return None

    def _draw_map(self, state: GameState) -> None:
        self._screen.blit(self._image(state.map.image_key), (0, 0))
        for route in state.routes:
            self._draw_route(route)
        for endpoint in state.endpoints:
            self._draw_endpoint(endpoint)
        self._draw_marker(
            self._image("base"),
            state.map.base.to_int_tuple(),
            "Base",
            above=False,
        )

    def _draw_route(self, route: Route) -> None:
        points = [point.to_int_tuple() for point in route.waypoints]
        pygame.draw.lines(self._screen, ROUTE_COLOR, False, points, 3)

    def _draw_endpoint(self, endpoint: Endpoint) -> None:
        self._draw_marker(
            self._image(endpoint.image_key),
            endpoint.position.to_int_tuple(),
            endpoint.name,
            above=True,
        )

    def _draw_rover(self, rover: Rover) -> None:
        image = self._image(rover.image_key)
        rect = image.get_rect(center=rover.position.to_int_tuple())
        self._screen.blit(image, rect)

    def _draw_marker(
        self,
        image: pygame.Surface,
        origin: tuple[int, int],
        label: str,
        *,
        above: bool,
    ) -> None:
        rect = image.get_rect(center=origin)
        self._screen.blit(image, rect)
        offset_y = -rect.height // 2 - 14 if above else rect.height // 2 + 14
        self._draw_label(label, origin, (0, offset_y))

    def _draw_buttons(self, state: GameState) -> None:
        for button in build_buttons(state, WINDOW_SIZE):
            enabled = button_enabled(
                button,
                state,
                self._selected_order,
                self._selected_rover,
            )
            selected = button_selected(
                button,
                self._selected_order,
                self._selected_rover,
            )
            if selected:
                color = BUTTON_SELECTED
            elif enabled:
                color = BUTTON_IDLE
            else:
                color = BUTTON_DISABLED
            pygame.draw.rect(self._screen, color, button.rect, border_radius=6)
            label = self._font.render(button.label, True, BUTTON_TEXT)
            self._screen.blit(label, label.get_rect(center=button.rect.center))

    def _draw_hud(self, state: GameState) -> None:
        y = 16
        money = self._font.render(f"Money  {state.money}", True, LABEL_COLOR)
        self._screen.blit(money, (24, y))
        y += 26
        order = self._selected_order
        if order is not None:
            detail = (
                f"{order.name}  {order.endpoint.name}  "
                f"wt {order.weight}  ${order.reward}"
            )
            line = self._font.render(detail, True, LABEL_COLOR)
            self._screen.blit(line, (24, y))
            y += 26
        for rover in state.rovers:
            y = self._draw_rover_stats(rover, 24, y)
        reason = confirm_reason(state, self._selected_order, self._selected_rover)
        if reason:
            text = self._font.render(reason, True, REASON_COLOR)
            self._screen.blit(text, (24, y + 4))

    def _draw_rover_stats(self, rover: Rover, x: int, y: int) -> int:
        label = f"{rover.id}  cap {rover.capacity}"
        line = self._font.render(label, True, LABEL_COLOR)
        self._screen.blit(line, (x, y))
        bar_x = x + 148
        self._draw_battery_bar(bar_x, y + 6, rover)
        battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
        amount = self._font.render(battery, True, LABEL_COLOR)
        self._screen.blit(amount, (bar_x + 92, y))
        return y + 24

    def _draw_battery_bar(self, x: int, y: int, rover: Rover) -> None:
        width, height = 80, 10
        pygame.draw.rect(self._screen, BATTERY_BACK, (x, y, width, height))
        if rover.battery_max <= 0:
            return
        fill = width * max(0.0, min(1.0, rover.battery / rover.battery_max))
        pygame.draw.rect(self._screen, BATTERY_FILL, (x, y, fill, height))

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
            if key == "map":
                loaded = pygame.transform.smoothscale(loaded, WINDOW_SIZE)
            else:
                loaded = _fit_sprite(loaded, SPRITE_MAX_SIZE[key])
            self._images[key] = loaded
        return loaded


def _fit_sprite(surface: pygame.Surface, max_size: int) -> pygame.Surface:
    bounds = surface.get_bounding_rect(min_alpha=127)
    if bounds.width == 0 or bounds.height == 0:
        return surface
    cropped = surface.subsurface(bounds).copy()
    width, height = cropped.get_size()
    scale = max_size / max(width, height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return pygame.transform.smoothscale(cropped, size)
