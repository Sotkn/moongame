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
from moon_game.geometry import Vec2
from moon_game.purchase import can_buy
from moon_game.ui.buttons import (
    Button,
    assignment_left_rect,
    assignment_park_viewport,
    assignment_reason_y,
    assignment_right_rect,
    assignment_scroll_max,
    assignment_title,
    build_buttons,
    button_enabled,
    button_selected,
    overlay_button_clip,
    overlay_reason,
    overlay_rect,
    rover_card_rect,
    shop_job_row_rect,
    shop_jobs_heading_y,
    shop_jobs_viewport,
    shop_left_rect,
    shop_offer_row_rect,
    shop_park_heading_y,
    shop_park_row_rect,
    shop_right_rect,
    shop_scroll_max,
    shop_scroll_step,
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

WINDOW_SIZE = (1280, 720)
MAP_LAYOUT_GUIDES = True
MAP_GUIDE_STEP = 100
ROUTE_AA = 4
ROUTE_DARK = (22, 18, 16)
ROUTE_LIGHT = (230, 220, 200)
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
    "poi2": 200,
    "poi3": 70,
    "poi4": 90,
    "poi5": 120,
}


class Ui:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Кризис лунного курьера")
        self._scale = 1.0
        self._window_size = WINDOW_SIZE
        self._screen = pygame.display.set_mode(WINDOW_SIZE)
        self._font = pygame.font.SysFont("segoe ui", 18)
        self._title_font = pygame.font.SysFont("segoe ui", 22)
        self._map_font = pygame.font.SysFont("segoe ui", 22, bold=True)
        self._images: dict[str, pygame.Surface] = {}
        self._selected_order_id: str | None = None
        self._selected_rover_id: str | None = None
        self._selected_route_id: str | None = None
        self._open_panel = OpenPanel.ASSIGNMENT
        self._shop_left_scroll = 0
        self._shop_right_scroll = 0
        self._assign_left_scroll = 0
        self._assign_right_scroll = 0
        self._last_phase: GamePhase | None = None
        self._last_pending: ChooseDelivery | None = None
        self._dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self._dim.fill(OVERLAY_DIM)
        self._route_overlays: dict[str | None, pygame.Surface] = {}

    def read_commands(
        self,
        events: Sequence[WindowEvent],
        state: GameState,
    ) -> list[PlayerCommand]:
        self._follow_state(state)
        self._clamp_panel_scroll(state)
        buttons = build_buttons(
            state,
            self._window_size,
            open_panel=self._open_panel,
            selected_order=self._selected_order(state),
            shop_left_scroll=self._shop_left_scroll,
            assign_left_scroll=self._assign_left_scroll,
            assign_right_scroll=self._assign_right_scroll,
        )
        commands: list[PlayerCommand] = []
        for event in events:
            if event.kind is WindowEventKind.SCROLL:
                self._scroll_panel(event, state)
                continue
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
        if MAP_LAYOUT_GUIDES:
            self._draw_map_guides()
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
        self._select_default_route(state, order)

    def _select_default_route(self, state: GameState, order: Order) -> None:
        candidates = routes_for_order(state, order)
        self._selected_route_id = candidates[0].id if candidates else None

    def _commands_from_click(
        self,
        event: WindowEvent,
        buttons: Sequence[Button],
        state: GameState,
    ) -> list[PlayerCommand]:
        if event.kind is not WindowEventKind.CLICK or event.position is None:
            return []
        overlay = overlay_rect(self._window_size)
        for button in buttons:
            if not button.rect.collidepoint(event.position):
                continue
            clip = overlay_button_clip(overlay, button.command)
            if clip is not None and not clip.collidepoint(event.position):
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
            if command.order_id == self._selected_order_id:
                return []
            self._selected_order_id = command.order_id
            order = self._selected_order(state)
            if order is None:
                self._selected_route_id = None
            else:
                self._select_default_route(state, order)
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
        if isinstance(command, StartDay):
            self._open_panel = OpenPanel.NONE
            return [command]
        if isinstance(command, (Pause, NextDay, EndDay)):
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

    def _scroll_panel(self, event: WindowEvent, state: GameState) -> None:
        if event.position is None:
            return
        overlay = overlay_rect(self._window_size)
        step = shop_scroll_step(overlay) * event.delta
        if self._open_panel is OpenPanel.SHOP:
            if shop_left_rect(overlay).collidepoint(event.position):
                self._shop_left_scroll -= step
            elif shop_right_rect(overlay).collidepoint(event.position):
                self._shop_right_scroll -= step
        elif self._open_panel is OpenPanel.ASSIGNMENT:
            if assignment_left_rect(overlay).collidepoint(event.position):
                self._assign_left_scroll -= step
            elif assignment_right_rect(overlay).collidepoint(event.position):
                self._assign_right_scroll -= step
        self._clamp_panel_scroll(state)

    def _clamp_panel_scroll(self, state: GameState) -> None:
        overlay = overlay_rect(self._window_size)
        shop_left_max, shop_right_max = shop_scroll_max(
            overlay,
            len(state.shop_offers),
            len(state.rovers),
            len(state.orders),
        )
        self._shop_left_scroll = max(0, min(self._shop_left_scroll, shop_left_max))
        self._shop_right_scroll = max(0, min(self._shop_right_scroll, shop_right_max))
        assign_left_max, assign_right_max = assignment_scroll_max(
            overlay, state, self._selected_order(state)
        )
        self._assign_left_scroll = max(
            0, min(self._assign_left_scroll, assign_left_max)
        )
        self._assign_right_scroll = max(
            0, min(self._assign_right_scroll, assign_right_max)
        )

    def _draw_map(self, state: GameState) -> None:
        self._screen.blit(self._image(state.map.image_key), (0, 0))
        highlighted = self._selected_route(state)
        self._screen.blit(self._routes_overlay(state, highlighted), (0, 0))
        for endpoint in state.endpoints:
            self._draw_endpoint(endpoint)
        self._draw_marker(
            self._image("base"),
            self._world_pos(state.map.base),
            "База",
            above=False,
        )

    def _routes_overlay(
        self,
        state: GameState,
        highlighted: Route | None,
    ) -> pygame.Surface:
        key = highlighted.id if highlighted is not None else None
        cached = self._route_overlays.get(key)
        if cached is not None:
            return cached
        overlay = self._render_routes(state.routes, highlighted)
        self._route_overlays[key] = overlay
        return overlay

    def _render_routes(
        self,
        routes: Sequence[Route],
        highlighted: Route | None,
    ) -> pygame.Surface:
        wide_size = (
            self._window_size[0] * ROUTE_AA,
            self._window_size[1] * ROUTE_AA,
        )
        wide = pygame.Surface(wide_size, pygame.SRCALPHA)
        for route in routes:
            if route is not highlighted:
                self._draw_route(wide, route, highlighted=False)
        if highlighted is not None:
            self._draw_route(wide, highlighted, highlighted=True)
        overlay = pygame.transform.smoothscale(wide, self._window_size)
        return overlay.convert_alpha()

    def _draw_route(
        self,
        surface: pygame.Surface,
        route: Route,
        *,
        highlighted: bool,
    ) -> None:
        points = [self._route_point(point) for point in route.waypoints]
        if highlighted:
            outer, inner, core = (
                self._px(16) * ROUTE_AA,
                self._px(12) * ROUTE_AA,
                self._px(3) * ROUTE_AA,
            )
        else:
            outer, inner, core = (
                self._px(12) * ROUTE_AA,
                self._px(8) * ROUTE_AA,
                self._px(2) * ROUTE_AA,
            )
        self._stroke_polyline(surface, points, ROUTE_DARK, outer)
        self._stroke_polyline(surface, points, ROUTE_LIGHT, inner)
        self._stroke_polyline(surface, points, ROUTE_DARK, core)

    def _stroke_polyline(
        self,
        surface: pygame.Surface,
        points: list[tuple[int, int]],
        color: tuple[int, int, int],
        width: int,
    ) -> None:
        pygame.draw.lines(surface, color, False, points, width)
        radius = width // 2
        if radius < 1:
            return
        for point in points:
            pygame.draw.circle(surface, color, point, radius)

    def _route_point(self, point: Vec2) -> tuple[int, int]:
        scale = self._scale * ROUTE_AA
        return (round(point.x * scale), round(point.y * scale))

    def _draw_endpoint(self, endpoint: Endpoint) -> None:
        self._draw_marker(
            self._image(endpoint.image_key),
            self._world_pos(endpoint.position),
            endpoint.name,
            above=True,
        )

    def _draw_rover(self, rover: Rover) -> None:
        image = self._image(rover.image_key)
        rect = image.get_rect(center=self._world_pos(rover.position))
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
        offset_y = (
            -rect.height // 2 - self._px(14)
            if above
            else rect.height // 2 + self._px(14)
        )
        self._draw_label(label, origin, (0, offset_y))

    def _draw_assignment(self, state: GameState) -> None:
        panel = self._draw_panel_frame()
        self._clamp_panel_scroll(state)
        title = self._title_font.render(assignment_title(state), True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + self._px(24), panel.y + self._px(20)))
        left = assignment_left_rect(panel)
        right = assignment_right_rect(panel)
        park = assignment_park_viewport(panel)
        park_heading = self._font.render("Парк", True, BUTTON_TEXT)
        jobs_heading = self._font.render("Заказы", True, BUTTON_TEXT)
        self._screen.blit(park_heading, (left.x, left.y))
        self._screen.blit(jobs_heading, (right.x, right.y))
        previous = self._screen.get_clip()
        self._screen.set_clip(park)
        for index, rover in enumerate(state.rovers):
            card = rover_card_rect(panel, index, self._assign_left_scroll)
            self._draw_rover_card(
                rover,
                card,
                selected=rover.id == self._selected_rover_id,
            )
        self._screen.set_clip(previous)
        reason = overlay_reason(
            state,
            self._selected_rover(state),
            self._selected_order(state),
            self._selected_route(state),
        )
        if reason:
            text = self._font.render(reason, True, REASON_COLOR)
            self._screen.blit(text, (left.x, assignment_reason_y(panel)))

    def _draw_shop(self, state: GameState) -> None:
        panel = self._draw_panel_frame()
        self._clamp_panel_scroll(state)
        title = self._title_font.render("Магазин", True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + self._px(24), panel.y + self._px(20)))
        previous = self._screen.get_clip()
        self._screen.set_clip(shop_left_rect(panel))
        self._draw_shop_offers(state, panel)
        self._draw_shop_park(state, panel)
        self._screen.set_clip(previous)
        jobs_view = shop_jobs_viewport(panel)
        heading = self._font.render("Заказы", True, BUTTON_TEXT)
        self._screen.blit(heading, (jobs_view.x, shop_jobs_heading_y(panel)))
        self._screen.set_clip(jobs_view)
        self._draw_shop_jobs(state, panel)
        self._screen.set_clip(previous)

    def _draw_panel_frame(self) -> pygame.Rect:
        self._screen.blit(self._dim, (0, 0))
        panel = overlay_rect(self._window_size)
        pygame.draw.rect(self._screen, PANEL_BG, panel, border_radius=self._px(10))
        pygame.draw.rect(
            self._screen,
            PANEL_BORDER,
            panel,
            width=self._px(2),
            border_radius=self._px(10),
        )
        return panel

    def _draw_shop_offers(self, state: GameState, panel: pygame.Rect) -> None:
        scroll = self._shop_left_scroll
        for index, offer in enumerate(state.shop_offers):
            row = shop_offer_row_rect(panel, index, scroll)
            pygame.draw.rect(
                self._screen, ROVER_CARD_BG, row, border_radius=self._px(6)
            )
            stats = self._font.render(_shop_label(offer), True, BUTTON_TEXT)
            result = can_buy(state, offer)
            if result.allowed:
                dest = stats.get_rect(midleft=(row.x + self._px(12), row.centery))
                self._screen.blit(stats, dest)
                continue
            self._screen.blit(stats, (row.x + self._px(12), row.y + self._px(6)))
            reason = self._font.render(result.reason, True, REASON_COLOR)
            self._screen.blit(reason, (row.x + self._px(12), row.y + self._px(28)))

    def _draw_shop_park(self, state: GameState, panel: pygame.Rect) -> None:
        offer_count = len(state.shop_offers)
        scroll = self._shop_left_scroll
        heading = self._font.render("Парк", True, BUTTON_TEXT)
        self._screen.blit(
            heading,
            (shop_left_rect(panel).x, shop_park_heading_y(panel, offer_count, scroll)),
        )
        if not state.rovers:
            empty = self._font.render("Нет", True, LABEL_COLOR)
            row = shop_park_row_rect(panel, offer_count, 0, scroll)
            self._screen.blit(
                empty,
                empty.get_rect(midleft=(row.x + self._px(12), row.centery)),
            )
            return
        for index, rover in enumerate(state.rovers):
            row = shop_park_row_rect(panel, offer_count, index, scroll)
            pygame.draw.rect(
                self._screen, ROVER_CARD_BG, row, border_radius=self._px(6)
            )
            line = self._font.render(_shop_park_label(rover), True, BUTTON_TEXT)
            self._screen.blit(
                line,
                line.get_rect(midleft=(row.x + self._px(12), row.centery)),
            )

    def _draw_shop_jobs(self, state: GameState, panel: pygame.Rect) -> None:
        scroll = self._shop_right_scroll
        if not state.orders:
            empty = self._font.render("Нет", True, LABEL_COLOR)
            row = shop_job_row_rect(panel, 0, scroll)
            self._screen.blit(
                empty,
                empty.get_rect(midleft=(row.x + self._px(12), row.centery)),
            )
            return
        for index, order in enumerate(state.orders):
            row = shop_job_row_rect(panel, index, scroll)
            pygame.draw.rect(
                self._screen, ROVER_CARD_BG, row, border_radius=self._px(6)
            )
            line = self._font.render(_shop_job_label(order), True, LABEL_COLOR)
            self._screen.blit(
                line,
                line.get_rect(midleft=(row.x + self._px(12), row.centery)),
            )

    def _draw_day_end(self, state: GameState) -> None:
        panel = self._draw_panel_frame()
        title = self._title_font.render("Конец дня", True, BUTTON_TEXT)
        self._screen.blit(title, (panel.x + self._px(24), panel.y + self._px(20)))
        money = self._font.render(f"Деньги  {state.money}", True, LABEL_COLOR)
        money_rect = money.get_rect(
            topright=(panel.right - self._px(24), panel.y + self._px(24))
        )
        self._screen.blit(money, money_rect)
        y = panel.y + self._px(64)
        y = self._draw_order_group(
            panel,
            y,
            "Выполнены",
            [order for order in state.orders if order.status is OrderStatus.COMPLETED],
        )
        y = self._draw_order_group(
            panel,
            y + self._px(16),
            "Провалены",
            [order for order in state.orders if order.status is OrderStatus.FAILED],
        )
        self._draw_order_group(
            panel,
            y + self._px(16),
            "Не выполнены",
            [
                order
                for order in state.orders
                if order.status not in (OrderStatus.COMPLETED, OrderStatus.FAILED)
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
        self._screen.blit(head, (panel.x + self._px(24), y))
        y += self._px(28)
        if not orders:
            empty = self._font.render("Нет", True, LABEL_COLOR)
            self._screen.blit(empty, (panel.x + self._px(24), y))
            return y + self._px(24)
        for order in orders:
            line = self._font.render(_summary_order_label(order), True, LABEL_COLOR)
            self._screen.blit(line, (panel.x + self._px(24), y))
            y += self._px(24)
        return y

    def _draw_rover_card(
        self,
        rover: Rover,
        rect: pygame.Rect,
        *,
        selected: bool,
    ) -> None:
        fill = BUTTON_SELECTED if selected else ROVER_CARD_BG
        pygame.draw.rect(self._screen, fill, rect, border_radius=self._px(8))
        if selected:
            pygame.draw.rect(
                self._screen,
                PANEL_BORDER,
                rect,
                width=self._px(2),
                border_radius=self._px(8),
            )
        name = self._font.render(rover.name, True, BUTTON_TEXT)
        self._screen.blit(name, (rect.x + self._px(12), rect.y + self._px(12)))
        status = self._font.render(_rover_status_label(rover), True, LABEL_COLOR)
        status_rect = status.get_rect(
            topright=(rect.right - self._px(12), rect.y + self._px(12))
        )
        self._screen.blit(status, status_rect)
        cap = self._font.render(f"груз {rover.capacity}", True, LABEL_COLOR)
        self._screen.blit(cap, (rect.x + self._px(12), rect.y + self._px(38)))
        bar_x = rect.x + self._px(88)
        self._draw_battery_bar(bar_x, rect.y + self._px(44), rover)
        battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
        amount = self._font.render(battery, True, LABEL_COLOR)
        self._screen.blit(amount, (bar_x + self._px(88), rect.y + self._px(38)))

    def _draw_buttons(self, state: GameState) -> None:
        overlay = overlay_rect(self._window_size)
        for button in build_buttons(
            state,
            self._window_size,
            open_panel=self._open_panel,
            selected_order=self._selected_order(state),
            shop_left_scroll=self._shop_left_scroll,
            assign_left_scroll=self._assign_left_scroll,
            assign_right_scroll=self._assign_right_scroll,
        ):
            if isinstance(button.command, SelectRover):
                continue
            clip = overlay_button_clip(overlay, button.command)
            previous = None
            if clip is not None:
                if not clip.colliderect(button.rect):
                    continue
                previous = self._screen.get_clip()
                self._screen.set_clip(clip)
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
            pygame.draw.rect(
                self._screen, color, button.rect, border_radius=self._px(6)
            )
            label = self._font.render(button.label, True, BUTTON_TEXT)
            if isinstance(button.command, (SelectOrder, SelectRoute)):
                dest = label.get_rect(
                    midleft=(button.rect.x + self._px(12), button.rect.centery)
                )
            else:
                dest = label.get_rect(center=button.rect.center)
            self._screen.blit(label, dest)
            if previous is not None:
                self._screen.set_clip(previous)

    def _draw_hud(self, state: GameState) -> None:
        remaining = max(0.0, state.day_length - state.day_elapsed)
        clock = f"День  {state.day_number}    Время  {remaining:.0f}ч"
        text = f"{clock}    Деньги  {state.money}"
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
            height += self._px(4) + notice.get_height()
        plate = pygame.Rect(
            self._px(16),
            self._px(8),
            width + 2 * self._px(HUD_PLATE_PAD_X),
            height + 2 * self._px(HUD_PLATE_PAD_Y),
        )
        pygame.draw.rect(self._screen, PANEL_BG, plate, border_radius=self._px(8))
        pygame.draw.rect(
            self._screen,
            PANEL_BORDER,
            plate,
            width=max(1, self._px(1)),
            border_radius=self._px(8),
        )
        self._screen.blit(
            line,
            (plate.x + self._px(HUD_PLATE_PAD_X), plate.y + self._px(HUD_PLATE_PAD_Y)),
        )
        if notice is not None:
            self._screen.blit(
                notice,
                (
                    plate.x + self._px(HUD_PLATE_PAD_X),
                    plate.y
                    + self._px(HUD_PLATE_PAD_Y)
                    + line.get_height()
                    + self._px(4),
                ),
            )
        if state.phase is GamePhase.DAY_END or self._open_panel is not OpenPanel.NONE:
            return
        y = plate.bottom + self._px(8)
        for rover in state.rovers:
            y = self._draw_rover_stats(rover, self._px(24), y)

    def _draw_rover_stats(self, rover: Rover, x: int, y: int) -> int:
        label = f"{rover.name}  груз {rover.capacity}"
        line = self._font.render(label, True, LABEL_COLOR)
        self._screen.blit(line, (x, y))
        bar_x = x + self._px(190)
        self._draw_battery_bar(bar_x, y + self._px(6), rover)
        battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
        amount = self._font.render(battery, True, LABEL_COLOR)
        self._screen.blit(amount, (bar_x + self._px(92), y))
        return y + self._px(24)

    def _draw_battery_bar(self, x: int, y: int, rover: Rover) -> None:
        width, height = self._px(80), self._px(10)
        pygame.draw.rect(self._screen, BATTERY_BACK, (x, y, width, height))
        if rover.battery_max <= 0:
            return
        fill = width * max(0.0, min(1.0, rover.battery / rover.battery_max))
        pygame.draw.rect(self._screen, BATTERY_FILL, (x, y, fill, height))

    def _draw_map_guides(self) -> None:
        width, height = self._window_size
        step = self._px(MAP_GUIDE_STEP)
        color = (255, 220, 80)
        for x in range(0, width, step):
            pygame.draw.line(self._screen, color, (x, 0), (x, height))
            self._screen.blit(self._font.render(str(x), True, color), (x + 4, 4))
        for y in range(0, height, step):
            pygame.draw.line(self._screen, color, (0, y), (width, y))
            if y != 0:
                self._screen.blit(self._font.render(str(y), True, color), (4, y + 4))
        mx, my = pygame.mouse.get_pos()
        world_x = round(mx / self._scale)
        world_y = round(my / self._scale)
        label = self._font.render(f"Vec2({world_x}, {world_y})", True, color)
        self._screen.blit(label, (mx + 14, my + 14))

    def _draw_label(
        self,
        text: str,
        origin: tuple[int, int],
        offset: tuple[int, int],
    ) -> None:
        surface = self._map_font.render(text, True, LABEL_COLOR)
        rect = surface.get_rect(
            center=(origin[0] + offset[0], origin[1] + offset[1]),
        )
        self._screen.blit(surface, rect)

    def _world_pos(self, point: Vec2) -> tuple[int, int]:
        return (round(point.x * self._scale), round(point.y * self._scale))

    def _px(self, value: int) -> int:
        return max(1, round(value * self._scale))

    def _image(self, key: str) -> pygame.Surface:
        loaded = self._images.get(key)
        if loaded is None:
            loaded = pygame.image.load(asset_path(key)).convert_alpha()
            if key == "map":
                loaded = pygame.transform.smoothscale(loaded, self._window_size)
            else:
                loaded = _fit_sprite(
                    loaded, max(1, round(SPRITE_MAX_SIZE[key] * self._scale))
                )
            self._images[key] = loaded
        return loaded


def _shop_label(offer: ShopOffer) -> str:
    stats = f"груз {offer.capacity}  бат {offer.battery_max:.0f}"
    return f"{offer.name}  {stats}  ${offer.price}"


def _shop_park_label(rover: Rover) -> str:
    battery = f"{rover.battery:.0f}/{rover.battery_max:.0f}"
    status = _rover_status_label(rover)
    return f"{rover.name}  груз {rover.capacity}  бат {battery}  {status}"


def _shop_job_label(order: Order) -> str:
    return f"{order.endpoint.name}  ${order.reward}"


def _summary_order_label(order: Order) -> str:
    return f"{order.name}  {order.endpoint.name}  ${order.reward}"


def _rover_status_label(rover: Rover) -> str:
    if rover.status is RoverStatus.IDLE:
        return "стоит"
    return "в рейсе"


def _fit_sprite(surface: pygame.Surface, max_size: int) -> pygame.Surface:
    bounds = surface.get_bounding_rect(min_alpha=127)
    if bounds.width == 0 or bounds.height == 0:
        return surface
    cropped = surface.subsurface(bounds).copy()
    width, height = cropped.get_size()
    scale = max_size / max(width, height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return pygame.transform.smoothscale(cropped, size)
