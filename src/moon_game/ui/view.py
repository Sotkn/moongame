from __future__ import annotations

from collections.abc import Sequence

import pygame

from moon_game.asset_catalog import asset_path
from moon_game.commands import (
    DismissChoice,
    Pause,
    PlayerCommand,
    ResumeFromChoice,
    StartDay,
    StartDelivery,
)
from moon_game.entities import ChooseDelivery, Endpoint, Order, Route, Rover
from moon_game.game_state import GamePhase, GameState
from moon_game.ui.buttons import (
    Button,
    build_buttons,
    button_enabled,
    button_selected,
    overlay_reason,
    overlay_rect,
    overlay_title,
    rover_card_rect,
)
from moon_game.ui.commands import Confirm, SelectOrder
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
OVERLAY_DIM = (8, 10, 16, 150)
PANEL_BG = (28, 34, 44)
PANEL_BORDER = (70, 92, 122)
ROVER_CARD_BG = (36, 42, 52)
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
        self._title_font = pygame.font.SysFont("segoe ui", 22)
        self._images: dict[str, pygame.Surface] = {}
        self._selected_order: Order | None = None
        self._dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self._dim.fill(OVERLAY_DIM)

    def read_commands(
        self,
        events: Sequence[WindowEvent],
        state: GameState,
    ) -> list[PlayerCommand]:
        if not state.overlay_open():
            self._selected_order = None
        buttons = build_buttons(state, WINDOW_SIZE)
        commands: list[PlayerCommand] = []
        for event in events:
            commands.extend(self._commands_from_click(event, buttons, state))
        return commands

    def draw(self, state: GameState) -> None:
        self._draw_map(state)
        for rover in state.rovers:
            self._draw_rover(rover)
        self._draw_hud(state)
        if state.overlay_open():
            self._draw_overlay(state)
        self._draw_buttons(state)
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()

    def _commands_from_click(
        self,
        event: WindowEvent,
        buttons: Sequence[Button],
        state: GameState,
    ) -> list[PlayerCommand]:
        if event.kind is not WindowEventKind.CLICK or event.position is None:
            return []
        for button in buttons:
            if not button.rect.collidepoint(event.position):
                continue
            if not button_enabled(button, state, self._selected_order):
                continue
            return self._commands_from_button(button, state)
        return []

    def _commands_from_button(
        self,
        button: Button,
        state: GameState,
    ) -> list[PlayerCommand]:
        command = button.command
        if isinstance(command, SelectOrder):
            self._selected_order = command.order
            return []
        if isinstance(command, Confirm):
            return self._commit_commands(state)
        if isinstance(command, (DismissChoice, Pause)):
            return [command]
        return []

    def _commit_commands(self, state: GameState) -> list[PlayerCommand]:
        order = self._selected_order
        if order is None:
            return []
        commands: list[PlayerCommand] = [StartDelivery(state.day_rover(), order)]
        if state.phase is GamePhase.DAY_START:
            commands.append(StartDay())
        elif isinstance(state.pending_event, ChooseDelivery):
            commands.append(ResumeFromChoice())
        return commands

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

    def _draw_overlay(self, state: GameState) -> None:
        self._screen.blit(self._dim, (0, 0))
        panel = overlay_rect(WINDOW_SIZE)
        pygame.draw.rect(self._screen, PANEL_BG, panel, border_radius=10)
        pygame.draw.rect(self._screen, PANEL_BORDER, panel, width=2, border_radius=10)
        title = self._title_font.render(overlay_title(state), True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + 24, panel.y + 20))
        money = self._font.render(f"Money  {state.money}", True, LABEL_COLOR)
        money_rect = money.get_rect(topright=(panel.right - 24, panel.y + 24))
        self._screen.blit(money, money_rect)
        card = rover_card_rect(panel, len(state.orders))
        self._draw_rover_card(state.day_rover(), card)
        reason = overlay_reason(state, self._selected_order)
        if reason:
            text = self._font.render(reason, True, REASON_COLOR)
            self._screen.blit(text, (card.x, card.bottom + 12))

    def _draw_rover_card(self, rover: Rover, rect: pygame.Rect) -> None:
        pygame.draw.rect(self._screen, ROVER_CARD_BG, rect, border_radius=8)
        name = self._font.render(rover.id, True, BUTTON_TEXT)
        self._screen.blit(name, (rect.x + 16, rect.y + 12))
        cap = self._font.render(f"cap {rover.capacity}", True, LABEL_COLOR)
        self._screen.blit(cap, (rect.x + 16, rect.y + 38))
        self._draw_battery_bar(rect.x + 148, rect.y + 44, rover)
        battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
        amount = self._font.render(battery, True, LABEL_COLOR)
        self._screen.blit(amount, (rect.x + 240, rect.y + 38))

    def _draw_buttons(self, state: GameState) -> None:
        for button in build_buttons(state, WINDOW_SIZE):
            enabled = button_enabled(button, state, self._selected_order)
            selected = button_selected(button, self._selected_order)
            if selected:
                color = BUTTON_SELECTED
            elif enabled:
                color = BUTTON_IDLE
            else:
                color = BUTTON_DISABLED
            pygame.draw.rect(self._screen, color, button.rect, border_radius=6)
            label = self._font.render(button.label, True, BUTTON_TEXT)
            if isinstance(button.command, SelectOrder):
                dest = label.get_rect(midleft=(button.rect.x + 12, button.rect.centery))
            else:
                dest = label.get_rect(center=button.rect.center)
            self._screen.blit(label, dest)

    def _draw_hud(self, state: GameState) -> None:
        if state.overlay_open():
            return
        money = self._font.render(f"Money  {state.money}", True, LABEL_COLOR)
        self._screen.blit(money, (24, 16))
        y = 42
        for rover in state.rovers:
            y = self._draw_rover_stats(rover, 24, y)

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
