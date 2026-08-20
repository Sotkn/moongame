from __future__ import annotations

from collections.abc import Sequence

import pygame

from moon_game.asset_catalog import asset_path
from moon_game.assignment import routes_for_order
from moon_game.commands import (
    BuyRover,
    DismissChoice,
    EndDay,
    NextDay,
    Pause,
    PlayerCommand,
    StartDay,
    StartDelivery,
)
from moon_game.entities import (
    ChooseDelivery,
    Endpoint,
    Order,
    OrderStatus,
    Route,
    Rover,
    RoverStatus,
    ShopOffer,
)
from moon_game.game_state import GamePhase, GameState
from moon_game.hazard import HIGH_RISK
from moon_game.purchase import can_buy
from moon_game.ui.buttons import (
    Button,
    assignment_title,
    build_buttons,
    button_enabled,
    button_selected,
    overlay_reason,
    overlay_rect,
    route_button_rect,
    rover_card_rect,
    shop_buy_rect,
    shop_job_row_rect,
    shop_jobs_heading_y,
    shop_offer_row_rect,
    shop_park_heading_y,
    shop_park_row_rect,
)
from moon_game.ui.commands import (
    Confirm,
    OpenPanel,
    SelectOrder,
    SelectRoute,
    SelectRover,
    ToggleAssign,
    ToggleShop,
)
from moon_game.window_events import WindowEvent, WindowEventKind

WINDOW_SIZE = (960, 540)
ROUTE_COLOR = (92, 98, 112)
ROUTE_HIGHLIGHT = (168, 196, 224)
ROUTE_HIGH_RISK = (196, 108, 72)
ROUTE_HIGH_RISK_HIGHLIGHT = (232, 168, 120)
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
HUD_PLATE_PAD_X = 12
HUD_PLATE_PAD_Y = 8
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
        self._selected_order_id: str | None = None
        self._selected_rover_id: str | None = None
        self._selected_route_id: str | None = None
        self._open_panel = OpenPanel.ASSIGNMENT
        self._last_phase: GamePhase | None = None
        self._last_pending: ChooseDelivery | None = None
        self._dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self._dim.fill(OVERLAY_DIM)

    def read_commands(
        self,
        events: Sequence[WindowEvent],
        state: GameState,
    ) -> list[PlayerCommand]:
        self._follow_state(state)
        buttons = build_buttons(
            state,
            WINDOW_SIZE,
            open_panel=self._open_panel,
            selected_order=self._selected_order(state),
        )
        commands: list[PlayerCommand] = []
        for event in events:
            commands.extend(self._commands_from_click(event, buttons, state))
        return commands

    def draw(self, state: GameState) -> None:
        self._follow_state(state)
        self._draw_map(state)
        for rover in state.rovers:
            self._draw_rover(rover)
        if state.phase is GamePhase.DAY_END:
            self._draw_day_end(state)
        elif self._open_panel is OpenPanel.ASSIGNMENT:
            self._draw_assignment(state)
        elif self._open_panel is OpenPanel.SHOP:
            self._draw_shop(state)
        self._draw_hud(state)
        self._draw_buttons(state)
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()

    def _follow_state(self, state: GameState) -> None:
        self._drop_stale_rover_highlight(state)
        pending = state.pending_event
        if isinstance(pending, ChooseDelivery) and pending != self._last_pending:
            self._open_panel = OpenPanel.ASSIGNMENT
            self._selected_rover_id = pending.rover.id
        if self._last_phase is GamePhase.DAY_END and state.phase is GamePhase.DAY_START:
            self._open_panel = OpenPanel.ASSIGNMENT
            self._selected_order_id = None
            self._selected_route_id = None
        if state.phase is GamePhase.DAY_END:
            self._open_panel = OpenPanel.NONE
        self._last_pending = state.pending_event
        self._last_phase = state.phase
        order = self._selected_order(state)
        if order is None or order.status is not OrderStatus.AVAILABLE:
            self._selected_order_id = None
            self._selected_route_id = None
            return
        self._highlight_route_for_order(state, order)

    def _drop_stale_rover_highlight(self, state: GameState) -> None:
        if self._selected_rover_id is None:
            return
        if self._selected_rover(state) is not None:
            return
        self._selected_rover_id = state.rovers[0].id if state.rovers else None

    def _selected_rover(self, state: GameState) -> Rover | None:
        rover_id = self._selected_rover_id
        if rover_id is None:
            return None
        return state.rover_by_id(rover_id)

    def _selected_order(self, state: GameState) -> Order | None:
        order_id = self._selected_order_id
        if order_id is None:
            return None
        return state.order_by_id(order_id)

    def _selected_route(self, state: GameState) -> Route | None:
        route_id = self._selected_route_id
        if route_id is None:
            return None
        for route in state.routes:
            if route.id == route_id:
                return route
        return None

    def _highlight_route_for_order(self, state: GameState, order: Order) -> None:
        candidates = routes_for_order(state, order)
        if not candidates:
            self._selected_route_id = None
            return
        current = self._selected_route(state)
        if current in candidates:
            return
        self._selected_route_id = candidates[0].id

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
            if not button_enabled(
                button,
                state,
                self._selected_rover(state),
                self._selected_order(state),
                self._selected_route(state),
            ):
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
            self._selected_order_id = command.order_id
            order = self._selected_order(state)
            if order is None:
                self._selected_route_id = None
            else:
                self._highlight_route_for_order(state, order)
            return []
        if isinstance(command, SelectRover):
            self._selected_rover_id = command.rover_id
            return []
        if isinstance(command, SelectRoute):
            self._selected_route_id = command.route_id
            return []
        if isinstance(command, Confirm):
            return self._send_command(state)
        if isinstance(command, ToggleAssign):
            return self._toggle_assign()
        if isinstance(command, ToggleShop):
            return self._toggle_shop()
        if isinstance(command, BuyRover):
            self._selected_rover_id = command.offer.id
            return [command]
        if isinstance(command, (Pause, StartDay, NextDay, EndDay)):
            return [command]
        return []

    def _send_command(self, state: GameState) -> list[PlayerCommand]:
        rover = self._selected_rover(state)
        order = self._selected_order(state)
        route = self._selected_route(state)
        if rover is None or order is None or route is None:
            return []
        return [StartDelivery(rover, order, route)]

    def _toggle_assign(self) -> list[PlayerCommand]:
        if self._open_panel is OpenPanel.ASSIGNMENT:
            self._open_panel = OpenPanel.NONE
            return [DismissChoice()]
        self._open_panel = OpenPanel.ASSIGNMENT
        return []

    def _toggle_shop(self) -> list[PlayerCommand]:
        if self._open_panel is OpenPanel.SHOP:
            self._open_panel = OpenPanel.NONE
            return []
        self._open_panel = OpenPanel.SHOP
        return []

    def _draw_map(self, state: GameState) -> None:
        self._screen.blit(self._image(state.map.image_key), (0, 0))
        highlighted = self._selected_route(state)
        for route in state.routes:
            if route is not highlighted:
                self._draw_route(route, highlighted=False)
        if highlighted is not None:
            self._draw_route(highlighted, highlighted=True)
        for endpoint in state.endpoints:
            self._draw_endpoint(endpoint)
        self._draw_marker(
            self._image("base"),
            state.map.base.to_int_tuple(),
            "Base",
            above=False,
        )

    def _draw_route(self, route: Route, *, highlighted: bool) -> None:
        points = [point.to_int_tuple() for point in route.waypoints]
        high_risk = route.risk >= HIGH_RISK
        if highlighted:
            color = ROUTE_HIGH_RISK_HIGHLIGHT if high_risk else ROUTE_HIGHLIGHT
        else:
            color = ROUTE_HIGH_RISK if high_risk else ROUTE_COLOR
        width = 5 if highlighted else 3
        pygame.draw.lines(self._screen, color, False, points, width)

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

    def _draw_assignment(self, state: GameState) -> None:
        panel = self._draw_panel_frame()
        title = self._title_font.render(assignment_title(state), True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + 24, panel.y + 20))
        rover_count = len(state.rovers)
        for index, rover in enumerate(state.rovers):
            card = rover_card_rect(panel, len(state.orders), index, rover_count)
            self._draw_rover_card(
                rover,
                card,
                selected=rover.id == self._selected_rover_id,
            )
        reason = overlay_reason(
            state,
            self._selected_rover(state),
            self._selected_order(state),
            self._selected_route(state),
        )
        if reason:
            text = self._font.render(reason, True, REASON_COLOR)
            reason_x = panel.x + 24
            reason_y = panel.y + 64
            if rover_count:
                card = rover_card_rect(panel, len(state.orders), 0, rover_count)
                reason_x = card.x
                reason_y = card.bottom + 12
            order = self._selected_order(state)
            routes = routes_for_order(state, order) if order is not None else []
            if routes:
                row = route_button_rect(
                    panel,
                    len(state.orders),
                    rover_count,
                    0,
                    len(routes),
                )
                reason_y = row.bottom + 12
            self._screen.blit(text, (reason_x, reason_y))

    def _draw_shop(self, state: GameState) -> None:
        panel = self._draw_panel_frame()
        title = self._title_font.render("Shop", True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + 24, panel.y + 20))
        self._draw_shop_offers(state, panel)
        self._draw_shop_park(state, panel)
        self._draw_shop_jobs(state, panel)

    def _draw_panel_frame(self) -> pygame.Rect:
        self._screen.blit(self._dim, (0, 0))
        panel = overlay_rect(WINDOW_SIZE)
        pygame.draw.rect(self._screen, PANEL_BG, panel, border_radius=10)
        pygame.draw.rect(self._screen, PANEL_BORDER, panel, width=2, border_radius=10)
        return panel

    def _draw_shop_offers(self, state: GameState, panel: pygame.Rect) -> None:
        for index, offer in enumerate(state.shop_offers):
            row = shop_offer_row_rect(panel, index)
            pygame.draw.rect(self._screen, ROVER_CARD_BG, row, border_radius=6)
            stats = self._font.render(_shop_label(offer), True, BUTTON_TEXT)
            self._screen.blit(
                stats,
                stats.get_rect(midleft=(row.x + 12, row.centery)),
            )
            result = can_buy(state, offer)
            if result.allowed:
                continue
            reason = self._font.render(result.reason, True, REASON_COLOR)
            buy = shop_buy_rect(panel, index)
            dest = reason.get_rect(midright=(buy.x - 12, row.centery))
            self._screen.blit(reason, dest)

    def _draw_shop_park(self, state: GameState, panel: pygame.Rect) -> None:
        offer_count = len(state.shop_offers)
        heading = self._font.render("Park", True, BUTTON_TEXT)
        self._screen.blit(
            heading,
            (panel.x + 24, shop_park_heading_y(panel, offer_count)),
        )
        if not state.rovers:
            empty = self._font.render("None", True, LABEL_COLOR)
            row = shop_park_row_rect(panel, offer_count, 0)
            self._screen.blit(empty, empty.get_rect(midleft=(row.x + 12, row.centery)))
            return
        for index, rover in enumerate(state.rovers):
            row = shop_park_row_rect(panel, offer_count, index)
            pygame.draw.rect(self._screen, ROVER_CARD_BG, row, border_radius=6)
            line = self._font.render(_shop_park_label(rover), True, BUTTON_TEXT)
            self._screen.blit(
                line,
                line.get_rect(midleft=(row.x + 12, row.centery)),
            )

    def _draw_shop_jobs(self, state: GameState, panel: pygame.Rect) -> None:
        offer_count = len(state.shop_offers)
        rover_count = len(state.rovers)
        heading = self._font.render("Jobs", True, BUTTON_TEXT)
        self._screen.blit(
            heading,
            (panel.x + 24, shop_jobs_heading_y(panel, offer_count, rover_count)),
        )
        if not state.orders:
            empty = self._font.render("None", True, LABEL_COLOR)
            row = shop_job_row_rect(panel, offer_count, rover_count, 0)
            self._screen.blit(empty, empty.get_rect(midleft=(row.x + 12, row.centery)))
            return
        for index, order in enumerate(state.orders):
            row = shop_job_row_rect(panel, offer_count, rover_count, index)
            pygame.draw.rect(self._screen, ROVER_CARD_BG, row, border_radius=6)
            line = self._font.render(_shop_job_label(order), True, LABEL_COLOR)
            self._screen.blit(
                line,
                line.get_rect(midleft=(row.x + 12, row.centery)),
            )

    def _draw_day_end(self, state: GameState) -> None:
        panel = self._draw_panel_frame()
        title = self._title_font.render("Day end", True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + 24, panel.y + 20))
        money = self._font.render(f"Money  {state.money}", True, LABEL_COLOR)
        money_rect = money.get_rect(topright=(panel.right - 24, panel.y + 24))
        self._screen.blit(money, money_rect)
        y = panel.y + 64
        y = self._draw_order_group(
            panel,
            y,
            "Completed",
            [order for order in state.orders if order.status is OrderStatus.COMPLETED],
        )
        self._draw_order_group(
            panel,
            y + 16,
            "Not completed",
            [
                order
                for order in state.orders
                if order.status is not OrderStatus.COMPLETED
            ],
        )

    def _draw_order_group(
        self,
        panel: pygame.Rect,
        y: int,
        heading: str,
        orders: Sequence[Order],
    ) -> int:
        head = self._font.render(heading, True, BUTTON_TEXT)
        self._screen.blit(head, (panel.x + 24, y))
        y += 28
        if not orders:
            empty = self._font.render("None", True, LABEL_COLOR)
            self._screen.blit(empty, (panel.x + 24, y))
            return y + 24
        for order in orders:
            line = self._font.render(_summary_order_label(order), True, LABEL_COLOR)
            self._screen.blit(line, (panel.x + 24, y))
            y += 24
        return y

    def _draw_rover_card(
        self,
        rover: Rover,
        rect: pygame.Rect,
        *,
        selected: bool,
    ) -> None:
        fill = BUTTON_SELECTED if selected else ROVER_CARD_BG
        pygame.draw.rect(self._screen, fill, rect, border_radius=8)
        if selected:
            pygame.draw.rect(self._screen, PANEL_BORDER, rect, width=2, border_radius=8)
        name = self._font.render(rover.id, True, BUTTON_TEXT)
        self._screen.blit(name, (rect.x + 12, rect.y + 12))
        status = self._font.render(_rover_status_label(rover), True, LABEL_COLOR)
        status_rect = status.get_rect(topright=(rect.right - 12, rect.y + 12))
        self._screen.blit(status, status_rect)
        cap = self._font.render(f"cap {rover.capacity}", True, LABEL_COLOR)
        self._screen.blit(cap, (rect.x + 12, rect.y + 38))
        bar_x = rect.x + 88
        self._draw_battery_bar(bar_x, rect.y + 44, rover)
        battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
        amount = self._font.render(battery, True, LABEL_COLOR)
        self._screen.blit(amount, (bar_x + 88, rect.y + 38))

    def _draw_buttons(self, state: GameState) -> None:
        for button in build_buttons(
            state,
            WINDOW_SIZE,
            open_panel=self._open_panel,
            selected_order=self._selected_order(state),
        ):
            if isinstance(button.command, SelectRover):
                continue
            enabled = button_enabled(
                button,
                state,
                self._selected_rover(state),
                self._selected_order(state),
                self._selected_route(state),
            )
            selected = button_selected(
                button,
                self._selected_order_id,
                self._selected_rover_id,
                self._selected_route_id,
                self._open_panel,
            )
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
        remaining = max(0.0, state.day_length - state.day_elapsed)
        text = (
            f"Day  {state.day_number}    Time  {remaining:.0f}s    Money  {state.money}"
        )
        line = self._font.render(text, True, LABEL_COLOR)
        notice = (
            self._font.render(state.hazard_notice, True, REASON_COLOR)
            if state.hazard_notice
            else None
        )
        width = line.get_width()
        height = line.get_height()
        if notice is not None:
            width = max(width, notice.get_width())
            height += 4 + notice.get_height()
        plate = pygame.Rect(
            16,
            8,
            width + 2 * HUD_PLATE_PAD_X,
            height + 2 * HUD_PLATE_PAD_Y,
        )
        pygame.draw.rect(self._screen, PANEL_BG, plate, border_radius=8)
        pygame.draw.rect(self._screen, PANEL_BORDER, plate, width=1, border_radius=8)
        self._screen.blit(line, (plate.x + HUD_PLATE_PAD_X, plate.y + HUD_PLATE_PAD_Y))
        if notice is not None:
            self._screen.blit(
                notice,
                (
                    plate.x + HUD_PLATE_PAD_X,
                    plate.y + HUD_PLATE_PAD_Y + line.get_height() + 4,
                ),
            )
        if state.phase is GamePhase.DAY_END or self._open_panel is not OpenPanel.NONE:
            return
        y = plate.bottom + 8
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


def _shop_label(offer: ShopOffer) -> str:
    return (
        f"{offer.id}  cap {offer.capacity}  bat {offer.battery_max:.0f}  ${offer.price}"
    )


def _shop_park_label(rover: Rover) -> str:
    battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
    status = _rover_status_label(rover)
    return f"{rover.id}  cap {rover.capacity}  bat {battery}  {status}"


def _shop_job_label(order: Order) -> str:
    return f"{order.endpoint.name}  ${order.reward}"


def _summary_order_label(order: Order) -> str:
    return f"{order.name}  {order.endpoint.name}  ${order.reward}"


def _rover_status_label(rover: Rover) -> str:
    if rover.status is RoverStatus.IDLE:
        return "idle"
    return "on a trip"


def _fit_sprite(surface: pygame.Surface, max_size: int) -> pygame.Surface:
    bounds = surface.get_bounding_rect(min_alpha=127)
    if bounds.width == 0 or bounds.height == 0:
        return surface
    cropped = surface.subsurface(bounds).copy()
    width, height = cropped.get_size()
    scale = max_size / max(width, height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return pygame.transform.smoothscale(cropped, size)
