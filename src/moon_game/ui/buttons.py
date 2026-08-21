from __future__ import annotations

from dataclasses import dataclass

import pygame

from moon_game.assignment import can_assign, routes_for_order
from moon_game.commands import BuyRover, EndDay, NextDay, Pause, StartDay
from moon_game.entities import Order, OrderStatus, Route, Rover, ShopOffer
from moon_game.game_state import GamePhase, GameState
from moon_game.hazard import risk_label
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
ROVER_CARD_INNER_GAP = 12
ROVER_CARD_HEIGHT = 72
BUTTON_SIZE = (140, 40)
BUTTON_GAP = 8
HUD_BUTTON_SIZE = (130, 36)
HUD_MARGIN = 16
HUD_BUTTON_Y = 8
SHOP_HEADING_HEIGHT = 22
SHOP_COMPACT_ROW = 28
SHOP_OFFER_ROW = 56
SHOP_SECTION_GAP = 12
SHOP_ROW_GAP = 4
SHOP_COLUMN_GAP = 16
SHOP_LEFT_NUM = 5
SHOP_LEFT_DEN = 8
SHOP_SCROLL_STEP = 36
ASSIGN_LEFT_NUM = 2
ASSIGN_LEFT_DEN = 5
ASSIGN_REASON_HEIGHT = 28
ASSIGN_ROUTE_INDENT = 16
ROUTE_ROW_HEIGHT = 36

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
    shop_left_scroll: int = 0,
    assign_left_scroll: int = 0,
    assign_right_scroll: int = 0,
) -> list[Button]:
    if state.phase is GamePhase.DAY_END:
        return [_next_day_button(window_size)]
    buttons = _hud_buttons(state, window_size)
    if open_panel is OpenPanel.ASSIGNMENT:
        buttons.extend(
            _assignment_buttons(
                state,
                window_size,
                selected_order,
                assign_left_scroll,
                assign_right_scroll,
            )
        )
    elif open_panel is OpenPanel.SHOP:
        buttons.extend(_shop_buttons(state, window_size, shop_left_scroll))
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
        return "Начало дня"
    return "Заказы"


def overlay_reason(
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
    selected_route: Route | None,
) -> str:
    if selected_rover is None:
        return "Выберите ровер"
    if selected_order is None:
        return "Выберите заказ"
    if selected_route is None:
        return "Выберите маршрут"
    result = can_assign(state, selected_rover, selected_order, selected_route)
    if result.allowed:
        return ""
    return result.reason


def overlay_rect(window_size: tuple[int, int]) -> pygame.Rect:
    width = _window_px(window_size, OVERLAY_SIZE[0])
    height = _window_px(window_size, OVERLAY_SIZE[1])
    return pygame.Rect(
        (window_size[0] - width) // 2,
        (window_size[1] - height) // 2,
        width,
        height,
    )


def overlay_content_rect(overlay: pygame.Rect, extra_bottom: int = 0) -> pygame.Rect:
    pad = _overlay_px(overlay, OVERLAY_PAD)
    top = overlay.y + pad + _overlay_px(overlay, TITLE_HEIGHT)
    action = _overlay_px(overlay, BUTTON_SIZE[1])
    bottom = (
        overlay.bottom - pad - action - _overlay_px(overlay, BUTTON_GAP) - extra_bottom
    )
    return pygame.Rect(overlay.x + pad, top, overlay.width - 2 * pad, bottom - top)


def shop_left_rect(overlay: pygame.Rect) -> pygame.Rect:
    return _split_columns(overlay, SHOP_LEFT_NUM, SHOP_LEFT_DEN)[0]


def shop_right_rect(overlay: pygame.Rect) -> pygame.Rect:
    return _split_columns(overlay, SHOP_LEFT_NUM, SHOP_LEFT_DEN)[1]


def shop_jobs_viewport(overlay: pygame.Rect) -> pygame.Rect:
    column = shop_right_rect(overlay)
    top = column.y + _overlay_px(overlay, SHOP_HEADING_HEIGHT)
    return pygame.Rect(column.x, top, column.width, column.bottom - top)


def shop_offer_row_rect(
    overlay: pygame.Rect,
    index: int,
    scroll: int = 0,
) -> pygame.Rect:
    column = shop_left_rect(overlay)
    height = _overlay_px(overlay, SHOP_OFFER_ROW)
    gap = _overlay_px(overlay, ROW_GAP)
    return pygame.Rect(
        column.x,
        column.y + index * (height + gap) - scroll,
        column.width,
        height,
    )


def shop_buy_rect(
    overlay: pygame.Rect,
    index: int,
    scroll: int = 0,
) -> pygame.Rect:
    row = shop_offer_row_rect(overlay, index, scroll)
    width = _overlay_px(overlay, BUTTON_SIZE[0])
    height = _overlay_px(overlay, BUTTON_SIZE[1])
    return pygame.Rect(
        row.right - width,
        row.y + (row.height - height) // 2,
        width,
        height,
    )


def shop_park_heading_y(
    overlay: pygame.Rect,
    offer_count: int,
    scroll: int = 0,
) -> int:
    column = shop_left_rect(overlay)
    if offer_count <= 0:
        return column.y - scroll
    last = shop_offer_row_rect(overlay, offer_count - 1, scroll=0)
    return last.bottom + _overlay_px(overlay, SHOP_SECTION_GAP) - scroll


def shop_park_row_rect(
    overlay: pygame.Rect,
    offer_count: int,
    index: int,
    scroll: int = 0,
) -> pygame.Rect:
    column = shop_left_rect(overlay)
    y = shop_park_heading_y(overlay, offer_count, scroll=0) + _overlay_px(
        overlay, SHOP_HEADING_HEIGHT
    )
    row = _overlay_px(overlay, SHOP_COMPACT_ROW)
    y += index * (row + _overlay_px(overlay, SHOP_ROW_GAP))
    return pygame.Rect(column.x, y - scroll, column.width, row)


def shop_jobs_heading_y(overlay: pygame.Rect) -> int:
    return shop_right_rect(overlay).y


def shop_job_row_rect(
    overlay: pygame.Rect,
    index: int,
    scroll: int = 0,
) -> pygame.Rect:
    viewport = shop_jobs_viewport(overlay)
    row = _overlay_px(overlay, SHOP_COMPACT_ROW)
    y = viewport.y + index * (row + _overlay_px(overlay, SHOP_ROW_GAP))
    return pygame.Rect(viewport.x, y - scroll, viewport.width, row)


def shop_scroll_max(
    overlay: pygame.Rect,
    offer_count: int,
    rover_count: int,
    order_count: int,
) -> tuple[int, int]:
    left = shop_left_rect(overlay)
    last_park = shop_park_row_rect(
        overlay, offer_count, max(0, rover_count - 1), scroll=0
    )
    left_max = max(0, last_park.bottom - left.y - left.height)
    jobs = shop_jobs_viewport(overlay)
    last_job = shop_job_row_rect(overlay, max(0, order_count - 1), scroll=0)
    right_max = max(0, last_job.bottom - jobs.y - jobs.height)
    return left_max, right_max


def shop_scroll_step(overlay: pygame.Rect) -> int:
    return _overlay_px(overlay, SHOP_SCROLL_STEP)


def assignment_left_rect(overlay: pygame.Rect) -> pygame.Rect:
    extra = _overlay_px(overlay, ASSIGN_REASON_HEIGHT)
    return _split_columns(overlay, ASSIGN_LEFT_NUM, ASSIGN_LEFT_DEN, extra)[0]


def assignment_right_rect(overlay: pygame.Rect) -> pygame.Rect:
    extra = _overlay_px(overlay, ASSIGN_REASON_HEIGHT)
    return _split_columns(overlay, ASSIGN_LEFT_NUM, ASSIGN_LEFT_DEN, extra)[1]


def assignment_park_viewport(overlay: pygame.Rect) -> pygame.Rect:
    return _column_viewport(overlay, assignment_left_rect(overlay))


def assignment_jobs_viewport(overlay: pygame.Rect) -> pygame.Rect:
    return _column_viewport(overlay, assignment_right_rect(overlay))


def assignment_reason_y(overlay: pygame.Rect) -> int:
    extra = _overlay_px(overlay, ASSIGN_REASON_HEIGHT)
    return overlay_content_rect(overlay, extra).bottom


def rover_card_rect(overlay: pygame.Rect, index: int, scroll: int = 0) -> pygame.Rect:
    view = assignment_park_viewport(overlay)
    height = _overlay_px(overlay, ROVER_CARD_HEIGHT)
    gap = _overlay_px(overlay, ROVER_CARD_INNER_GAP)
    return pygame.Rect(
        view.x,
        view.y + index * (height + gap) - scroll,
        view.width,
        height,
    )


def assignment_order_row_rect(
    overlay: pygame.Rect,
    state: GameState,
    selected_order: Order | None,
    index: int,
    scroll: int = 0,
) -> pygame.Rect:
    view = assignment_jobs_viewport(overlay)
    y = _assignment_order_top(overlay, state, selected_order, index)
    return pygame.Rect(
        view.x,
        y - scroll,
        view.width,
        _overlay_px(overlay, ROW_HEIGHT),
    )


def route_button_rect(
    overlay: pygame.Rect,
    state: GameState,
    selected_order: Order,
    index: int,
    scroll: int = 0,
) -> pygame.Rect:
    view = assignment_jobs_viewport(overlay)
    order_index = state.orders.index(selected_order)
    order_row = assignment_order_row_rect(
        overlay, state, selected_order, order_index, scroll=0
    )
    indent = _overlay_px(overlay, ASSIGN_ROUTE_INDENT)
    height = _overlay_px(overlay, ROUTE_ROW_HEIGHT)
    gap = _overlay_px(overlay, SHOP_ROW_GAP)
    y = order_row.bottom + gap + index * (height + gap)
    return pygame.Rect(
        view.x + indent,
        y - scroll,
        view.width - indent,
        height,
    )


def assignment_scroll_max(
    overlay: pygame.Rect,
    state: GameState,
    selected_order: Order | None,
) -> tuple[int, int]:
    park = assignment_park_viewport(overlay)
    if state.rovers:
        last_rover = rover_card_rect(overlay, len(state.rovers) - 1, scroll=0)
        left_max = max(0, last_rover.bottom - park.y - park.height)
    else:
        left_max = 0
    jobs = assignment_jobs_viewport(overlay)
    y = jobs.y
    for order in state.orders:
        y += _assignment_block_height(overlay, state, selected_order, order)
    right_max = max(0, y - jobs.y - jobs.height)
    return left_max, right_max


def overlay_button_clip(
    overlay: pygame.Rect,
    command: ButtonCommand,
) -> pygame.Rect | None:
    if isinstance(command, BuyRover):
        return shop_left_rect(overlay)
    if isinstance(command, SelectRover):
        return assignment_park_viewport(overlay)
    if isinstance(command, (SelectOrder, SelectRoute)):
        return assignment_jobs_viewport(overlay)
    return None


def _hud_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    width = _window_px(window_size, HUD_BUTTON_SIZE[0])
    height = _window_px(window_size, HUD_BUTTON_SIZE[1])
    x = window_size[0] - _window_px(window_size, HUD_MARGIN)
    y = _window_px(window_size, HUD_BUTTON_Y)
    gap = _window_px(window_size, BUTTON_GAP)
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
        x -= gap

    add("end-day", "Конец дня", EndDay())
    if state.phase is GamePhase.RUNNING:
        add("pause", "Продолжить" if state.paused else "Пауза", Pause())
    add("shop", "Магазин", ToggleShop())
    add("assign", "Заказы", ToggleAssign())
    return buttons


def _assignment_buttons(
    state: GameState,
    window_size: tuple[int, int],
    selected_order: Order | None,
    left_scroll: int,
    right_scroll: int,
) -> list[Button]:
    overlay = overlay_rect(window_size)
    buttons = _order_rows(state, overlay, selected_order, right_scroll)
    buttons.extend(_rover_cards(state, overlay, left_scroll))
    buttons.extend(_route_buttons(state, overlay, selected_order, right_scroll))
    close_index = 2 if state.phase is GamePhase.DAY_START else 1
    buttons.append(_close_button(overlay, close_index, ToggleAssign()))
    if state.phase is GamePhase.DAY_START:
        buttons.append(_start_day_button(overlay))
    buttons.append(_send_button(overlay))
    return buttons


def _shop_buttons(
    state: GameState,
    window_size: tuple[int, int],
    left_scroll: int,
) -> list[Button]:
    overlay = overlay_rect(window_size)
    buttons = _shop_buy_rows(state, overlay, left_scroll)
    buttons.append(_close_button(overlay, 0, ToggleShop()))
    return buttons


def _order_rows(
    state: GameState,
    overlay: pygame.Rect,
    selected_order: Order | None,
    scroll: int,
) -> list[Button]:
    buttons: list[Button] = []
    for index, order in enumerate(state.orders):
        buttons.append(
            Button(
                id=f"order-{order.id}",
                rect=assignment_order_row_rect(
                    overlay, state, selected_order, index, scroll
                ),
                label=_order_label(order, state.day_elapsed),
                command=SelectOrder(order.id),
            )
        )
    return buttons


def _shop_buy_rows(
    state: GameState,
    overlay: pygame.Rect,
    left_scroll: int,
) -> list[Button]:
    buttons: list[Button] = []
    for index, offer in enumerate(state.shop_offers):
        buttons.append(
            Button(
                id=f"buy-{offer.id}",
                rect=shop_buy_rect(overlay, index, left_scroll),
                label="Купить",
                command=BuyRover(offer),
            )
        )
    return buttons


def _rover_cards(
    state: GameState,
    overlay: pygame.Rect,
    scroll: int,
) -> list[Button]:
    buttons: list[Button] = []
    for index, rover in enumerate(state.rovers):
        buttons.append(
            Button(
                id=f"rover-{rover.id}",
                rect=rover_card_rect(overlay, index, scroll),
                label=rover.name,
                command=SelectRover(rover.id),
            )
        )
    return buttons


def _route_buttons(
    state: GameState,
    overlay: pygame.Rect,
    selected_order: Order | None,
    scroll: int,
) -> list[Button]:
    if selected_order is None:
        return []
    routes = routes_for_order(state, selected_order)
    buttons: list[Button] = []
    for index, route in enumerate(routes):
        buttons.append(
            Button(
                id=f"route-{route.id}",
                rect=route_button_rect(overlay, state, selected_order, index, scroll),
                label=_route_label(route),
                command=SelectRoute(route.id),
            )
        )
    return buttons


def _send_button(overlay: pygame.Rect) -> Button:
    return Button(
        id="send",
        rect=_overlay_action_rect(overlay, 0),
        label="Отправить",
        command=Confirm(),
    )


def _start_day_button(overlay: pygame.Rect) -> Button:
    return Button(
        id="start-day",
        rect=_overlay_action_rect(overlay, 1),
        label="Начать день",
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
        label="Закрыть",
        command=command,
    )


def _next_day_button(window_size: tuple[int, int]) -> Button:
    overlay = overlay_rect(window_size)
    return Button(
        id="next-day",
        rect=_overlay_action_rect(overlay, 0),
        label="Новый день",
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
    width = _overlay_px(overlay, BUTTON_SIZE[0])
    height = _overlay_px(overlay, BUTTON_SIZE[1])
    pad = _overlay_px(overlay, OVERLAY_PAD)
    x = overlay.right - pad - (index_from_right + 1) * width
    x -= index_from_right * _overlay_px(overlay, BUTTON_GAP)
    return pygame.Rect(
        x,
        overlay.bottom - pad - height,
        width,
        height,
    )


def _split_columns(
    overlay: pygame.Rect,
    left_num: int,
    left_den: int,
    extra_bottom: int = 0,
) -> tuple[pygame.Rect, pygame.Rect]:
    content = overlay_content_rect(overlay, extra_bottom)
    gap = _overlay_px(overlay, SHOP_COLUMN_GAP)
    width = (content.width - gap) * left_num // left_den
    left = pygame.Rect(content.x, content.y, width, content.height)
    x = left.right + gap
    right = pygame.Rect(x, content.y, content.right - x, content.height)
    return left, right


def _column_viewport(overlay: pygame.Rect, column: pygame.Rect) -> pygame.Rect:
    top = column.y + _overlay_px(overlay, SHOP_HEADING_HEIGHT)
    return pygame.Rect(column.x, top, column.width, column.bottom - top)


def _assignment_order_top(
    overlay: pygame.Rect,
    state: GameState,
    selected_order: Order | None,
    index: int,
) -> int:
    y = assignment_jobs_viewport(overlay).y
    for i, order in enumerate(state.orders):
        if i == index:
            return y
        y += _assignment_block_height(overlay, state, selected_order, order)
    return y


def _assignment_block_height(
    overlay: pygame.Rect,
    state: GameState,
    selected_order: Order | None,
    order: Order,
) -> int:
    height = _overlay_px(overlay, ROW_HEIGHT) + _overlay_px(overlay, ROW_GAP)
    if selected_order is None or order.id != selected_order.id:
        return height
    routes = routes_for_order(state, order)
    if not routes:
        return height
    route_h = _overlay_px(overlay, ROUTE_ROW_HEIGHT)
    route_gap = _overlay_px(overlay, SHOP_ROW_GAP)
    return height + route_gap + len(routes) * (route_h + route_gap)


def _overlay_px(overlay: pygame.Rect, value: int) -> int:
    return max(1, round(value * overlay.width / OVERLAY_SIZE[0]))


def _window_px(window_size: tuple[int, int], value: int) -> int:
    return max(1, round(value * window_size[0] / 1280))


def _order_label(order: Order, day_elapsed: float) -> str:
    remaining = max(0.0, order.deadline - day_elapsed)
    return (
        f"{order.name}  {order.endpoint.name}  "
        f"вес {order.weight}  ${order.reward}  "
        f"срок {remaining:.0f}ч  {_order_status_label(order)}"
    )


def _order_status_label(order: Order) -> str:
    if order.status is OrderStatus.AVAILABLE:
        return "доступен"
    if order.status is OrderStatus.IN_PROGRESS:
        return "в работе"
    if order.status is OrderStatus.COMPLETED:
        return "выполнен"
    return "провален"


def _route_label(route: Route) -> str:
    return f"{route.name}  {route.length:.0f}  {risk_label(route)}"
