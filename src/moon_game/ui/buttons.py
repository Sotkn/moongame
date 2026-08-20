from __future__ import annotations

from dataclasses import dataclass

import pygame

from moon_game.assignment import can_assign, routes_for_order
from moon_game.commands import BuyRover, EndDay, NextDay, Pause, StartDay
from moon_game.entities import Order, Route, Rover, ShopOffer
from moon_game.game_state import GamePhase, GameState
from moon_game.purchase import can_buy
from moon_game.ui.commands import (
    Confirm,
    OpenPanel,
    SelectOrder,
    SelectRoute,
    SelectRover,
    ToggleAssign,
    ToggleShop,
)

OVERLAY_SIZE = (800, 480)
OVERLAY_PAD = 24
TITLE_HEIGHT = 32
ROW_HEIGHT = 40
ROW_GAP = 8
ROVER_CARD_GAP = 16
ROVER_CARD_INNER_GAP = 12
ROVER_CARD_HEIGHT = 72
BUTTON_SIZE = (140, 40)
BUTTON_GAP = 8
HUD_BUTTON_SIZE = (112, 36)
HUD_MARGIN = 16
HUD_BUTTON_Y = 8
SHOP_HEADING_HEIGHT = 22
SHOP_COMPACT_ROW = 28
SHOP_SECTION_GAP = 12
SHOP_ROW_GAP = 4
ROUTE_ROW_HEIGHT = 36
ROUTE_ROW_GAP = 12

type ButtonCommand = (
    SelectOrder
    | SelectRover
    | SelectRoute
    | Confirm
    | Pause
    | StartDay
    | NextDay
    | ToggleAssign
    | ToggleShop
    | BuyRover
    | EndDay
)


@dataclass
class Button:
    id: str
    rect: pygame.Rect
    label: str
    command: ButtonCommand


def build_buttons(
    state: GameState,
    window_size: tuple[int, int],
    *,
    open_panel: OpenPanel,
    selected_order: Order | None = None,
) -> list[Button]:
    if state.phase is GamePhase.DAY_END:
        return [_next_day_button(window_size)]
    buttons = _hud_buttons(state, window_size)
    if open_panel is OpenPanel.ASSIGNMENT:
        buttons.extend(_assignment_buttons(state, window_size, selected_order))
    elif open_panel is OpenPanel.SHOP:
        buttons.extend(_shop_buttons(state, window_size))
    return buttons


def button_enabled(
    button: Button,
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
    selected_route: Route | None,
) -> bool:
    command = button.command
    if isinstance(command, Confirm):
        return _send_enabled(state, selected_rover, selected_order, selected_route)
    if isinstance(command, StartDay):
        return state.phase is GamePhase.DAY_START
    if isinstance(command, NextDay):
        return state.phase is GamePhase.DAY_END
    if isinstance(command, BuyRover):
        return _buy_enabled(state, command.offer)
    if isinstance(command, EndDay):
        return state.phase in (GamePhase.DAY_START, GamePhase.RUNNING)
    return isinstance(
        command,
        (SelectOrder, SelectRover, SelectRoute, Pause, ToggleAssign, ToggleShop),
    )


def button_selected(
    button: Button,
    selected_order_id: str | None,
    selected_rover_id: str | None,
    selected_route_id: str | None,
    open_panel: OpenPanel,
) -> bool:
    if isinstance(button.command, SelectOrder):
        return button.command.order_id == selected_order_id
    if isinstance(button.command, SelectRover):
        return button.command.rover_id == selected_rover_id
    if isinstance(button.command, SelectRoute):
        return button.command.route_id == selected_route_id
    if isinstance(button.command, ToggleAssign):
        return open_panel is OpenPanel.ASSIGNMENT
    if isinstance(button.command, ToggleShop):
        return open_panel is OpenPanel.SHOP
    return False


def assignment_title(state: GameState) -> str:
    if state.phase is GamePhase.DAY_START:
        return "Day start"
    return "Orders"


def overlay_reason(
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
    selected_route: Route | None,
) -> str:
    if selected_rover is None:
        return "Select a rover"
    if selected_order is None:
        return "Select an order"
    if selected_route is None:
        return "Select a route"
    result = can_assign(state, selected_rover, selected_order, selected_route)
    if result.allowed:
        return ""
    return result.reason


def overlay_rect(window_size: tuple[int, int]) -> pygame.Rect:
    width, height = OVERLAY_SIZE
    return pygame.Rect(
        (window_size[0] - width) // 2,
        (window_size[1] - height) // 2,
        width,
        height,
    )


def shop_offer_row_rect(overlay: pygame.Rect, index: int) -> pygame.Rect:
    return _content_row_rect(overlay, index, ROW_HEIGHT, ROW_GAP)


def shop_buy_rect(overlay: pygame.Rect, index: int) -> pygame.Rect:
    row = shop_offer_row_rect(overlay, index)
    width, height = BUTTON_SIZE
    return pygame.Rect(
        row.right - width,
        row.y,
        width,
        height,
    )


def shop_park_heading_y(overlay: pygame.Rect, offer_count: int) -> int:
    return _rows_bottom(overlay, offer_count, ROW_HEIGHT, ROW_GAP) + SHOP_SECTION_GAP


def shop_park_row_rect(
    overlay: pygame.Rect,
    offer_count: int,
    index: int,
) -> pygame.Rect:
    y = shop_park_heading_y(overlay, offer_count) + SHOP_HEADING_HEIGHT
    y += index * (SHOP_COMPACT_ROW + SHOP_ROW_GAP)
    return pygame.Rect(
        overlay.x + OVERLAY_PAD,
        y,
        overlay.width - 2 * OVERLAY_PAD,
        SHOP_COMPACT_ROW,
    )


def shop_jobs_heading_y(
    overlay: pygame.Rect,
    offer_count: int,
    rover_count: int,
) -> int:
    last_park = max(0, rover_count - 1)
    park_bottom = shop_park_row_rect(overlay, offer_count, last_park).bottom
    return park_bottom + SHOP_SECTION_GAP


def shop_job_row_rect(
    overlay: pygame.Rect,
    offer_count: int,
    rover_count: int,
    index: int,
) -> pygame.Rect:
    y = shop_jobs_heading_y(overlay, offer_count, rover_count) + SHOP_HEADING_HEIGHT
    y += index * (SHOP_COMPACT_ROW + SHOP_ROW_GAP)
    return pygame.Rect(
        overlay.x + OVERLAY_PAD,
        y,
        overlay.width - 2 * OVERLAY_PAD,
        SHOP_COMPACT_ROW,
    )


def rover_card_rect(
    overlay: pygame.Rect,
    order_count: int,
    index: int,
    rover_count: int,
) -> pygame.Rect:
    y = _rows_bottom(overlay, order_count, ROW_HEIGHT, ROW_GAP) + ROVER_CARD_GAP
    inner_width = overlay.width - 2 * OVERLAY_PAD
    count = max(1, rover_count)
    gap = ROVER_CARD_INNER_GAP if count > 1 else 0
    width = (inner_width - gap * (count - 1)) // count
    x = overlay.x + OVERLAY_PAD + index * (width + gap)
    return pygame.Rect(x, y, width, ROVER_CARD_HEIGHT)


def route_button_rect(
    overlay: pygame.Rect,
    order_count: int,
    rover_count: int,
    index: int,
    route_count: int,
) -> pygame.Rect:
    y = rover_card_rect(overlay, order_count, 0, rover_count).bottom + ROUTE_ROW_GAP
    inner_width = overlay.width - 2 * OVERLAY_PAD
    count = max(1, route_count)
    gap = ROVER_CARD_INNER_GAP if count > 1 else 0
    width = (inner_width - gap * (count - 1)) // count
    x = overlay.x + OVERLAY_PAD + index * (width + gap)
    return pygame.Rect(x, y, width, ROUTE_ROW_HEIGHT)


def _hud_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    width, height = HUD_BUTTON_SIZE
    x = window_size[0] - HUD_MARGIN
    y = HUD_BUTTON_Y
    buttons: list[Button] = []

    def add(button_id: str, label: str, command: ButtonCommand) -> None:
        nonlocal x
        x -= width
        buttons.append(
            Button(
                id=button_id,
                rect=pygame.Rect(x, y, width, height),
                label=label,
                command=command,
            )
        )
        x -= BUTTON_GAP

    add("end-day", "End day", EndDay())
    if state.phase is GamePhase.RUNNING:
        add("pause", "Resume" if state.paused else "Pause", Pause())
    add("shop", "Shop", ToggleShop())
    add("assign", "Assign", ToggleAssign())
    return buttons


def _assignment_buttons(
    state: GameState,
    window_size: tuple[int, int],
    selected_order: Order | None,
) -> list[Button]:
    overlay = overlay_rect(window_size)
    buttons = _order_rows(state, overlay)
    buttons.extend(_rover_cards(state, overlay))
    buttons.extend(_route_buttons(state, overlay, selected_order))
    close_index = 2 if state.phase is GamePhase.DAY_START else 1
    buttons.append(_close_button(overlay, close_index, ToggleAssign()))
    if state.phase is GamePhase.DAY_START:
        buttons.append(_start_day_button(overlay))
    buttons.append(_send_button(overlay))
    return buttons


def _shop_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    overlay = overlay_rect(window_size)
    buttons = _shop_buy_rows(state, overlay)
    buttons.append(_close_button(overlay, 0, ToggleShop()))
    return buttons


def _order_rows(state: GameState, overlay: pygame.Rect) -> list[Button]:
    buttons: list[Button] = []
    for index, order in enumerate(state.orders):
        buttons.append(
            Button(
                id=f"order-{order.id}",
                rect=_content_row_rect(overlay, index, ROW_HEIGHT, ROW_GAP),
                label=_order_label(order),
                command=SelectOrder(order.id),
            )
        )
    return buttons


def _shop_buy_rows(state: GameState, overlay: pygame.Rect) -> list[Button]:
    buttons: list[Button] = []
    for index, offer in enumerate(state.shop_offers):
        buttons.append(
            Button(
                id=f"buy-{offer.id}",
                rect=shop_buy_rect(overlay, index),
                label="Buy",
                command=BuyRover(offer),
            )
        )
    return buttons


def _rover_cards(state: GameState, overlay: pygame.Rect) -> list[Button]:
    buttons: list[Button] = []
    rover_count = len(state.rovers)
    for index, rover in enumerate(state.rovers):
        buttons.append(
            Button(
                id=f"rover-{rover.id}",
                rect=rover_card_rect(
                    overlay,
                    len(state.orders),
                    index,
                    rover_count,
                ),
                label=rover.id,
                command=SelectRover(rover.id),
            )
        )
    return buttons


def _route_buttons(
    state: GameState,
    overlay: pygame.Rect,
    selected_order: Order | None,
) -> list[Button]:
    if selected_order is None:
        return []
    routes = routes_for_order(state, selected_order)
    rover_count = len(state.rovers)
    order_count = len(state.orders)
    buttons: list[Button] = []
    for index, route in enumerate(routes):
        buttons.append(
            Button(
                id=f"route-{route.id}",
                rect=route_button_rect(
                    overlay,
                    order_count,
                    rover_count,
                    index,
                    len(routes),
                ),
                label=_route_label(route),
                command=SelectRoute(route.id),
            )
        )
    return buttons


def _send_button(overlay: pygame.Rect) -> Button:
    return Button(
        id="send",
        rect=_overlay_action_rect(overlay, 0),
        label="Send",
        command=Confirm(),
    )


def _start_day_button(overlay: pygame.Rect) -> Button:
    return Button(
        id="start-day",
        rect=_overlay_action_rect(overlay, 1),
        label="Start day",
        command=StartDay(),
    )


def _close_button(
    overlay: pygame.Rect,
    index_from_right: int,
    command: ToggleAssign | ToggleShop,
) -> Button:
    return Button(
        id="close",
        rect=_overlay_action_rect(overlay, index_from_right),
        label="Close",
        command=command,
    )


def _next_day_button(window_size: tuple[int, int]) -> Button:
    overlay = overlay_rect(window_size)
    return Button(
        id="next-day",
        rect=_overlay_action_rect(overlay, 0),
        label="Next day",
        command=NextDay(),
    )


def _send_enabled(
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
    selected_route: Route | None,
) -> bool:
    if state.phase not in (GamePhase.DAY_START, GamePhase.RUNNING):
        return False
    if selected_rover is None or selected_order is None or selected_route is None:
        return False
    return can_assign(state, selected_rover, selected_order, selected_route).allowed


def _buy_enabled(state: GameState, offer: ShopOffer) -> bool:
    if state.phase not in (GamePhase.DAY_START, GamePhase.RUNNING):
        return False
    return can_buy(state, offer).allowed


def _overlay_action_rect(overlay: pygame.Rect, index_from_right: int) -> pygame.Rect:
    width, height = BUTTON_SIZE
    x = overlay.right - OVERLAY_PAD - (index_from_right + 1) * width
    x -= index_from_right * BUTTON_GAP
    return pygame.Rect(
        x,
        overlay.bottom - OVERLAY_PAD - height,
        width,
        height,
    )


def _content_row_rect(
    overlay: pygame.Rect,
    index: int,
    height: int,
    gap: int,
) -> pygame.Rect:
    y = overlay.y + OVERLAY_PAD + TITLE_HEIGHT + index * (height + gap)
    return pygame.Rect(
        overlay.x + OVERLAY_PAD,
        y,
        overlay.width - 2 * OVERLAY_PAD,
        height,
    )


def _rows_bottom(
    overlay: pygame.Rect,
    count: int,
    height: int,
    gap: int,
) -> int:
    if count <= 0:
        return overlay.y + OVERLAY_PAD + TITLE_HEIGHT
    return _content_row_rect(overlay, count - 1, height, gap).bottom


def _order_label(order: Order) -> str:
    return (
        f"{order.name}  {order.endpoint.name}  "
        f"wt {order.weight}  ${order.reward}  {order.status.value}"
    )


def _route_label(route: Route) -> str:
    return f"{route.name}  {route.length:.0f}"
