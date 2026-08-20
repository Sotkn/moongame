from __future__ import annotations

from dataclasses import dataclass

import pygame

from moon_game.assignment import can_assign
from moon_game.commands import NextDay, Pause, StartDay
from moon_game.entities import Order, Rover
from moon_game.game_state import GamePhase, GameState
from moon_game.ui.commands import Confirm, SelectOrder, ToggleOrders

OVERLAY_SIZE = (700, 440)
OVERLAY_PAD = 24
TITLE_HEIGHT = 32
ROW_HEIGHT = 40
ROW_GAP = 8
ROVER_CARD_GAP = 16
ROVER_CARD_HEIGHT = 72
BUTTON_SIZE = (140, 40)
BUTTON_GAP = 8
HUD_BUTTON_SIZE = (112, 36)
HUD_MARGIN = 16
HUD_BUTTON_Y = 8

type ButtonCommand = (
    SelectOrder | Confirm | Pause | StartDay | NextDay | ToggleOrders
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
    orders_open: bool,
) -> list[Button]:
    if state.phase is GamePhase.DAY_END:
        return [_next_day_button(window_size)]
    buttons = _hud_buttons(state, window_size)
    if orders_open:
        buttons.extend(_overlay_buttons(state, window_size))
    return buttons


def button_enabled(
    button: Button,
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
) -> bool:
    command = button.command
    if isinstance(command, Confirm):
        return _send_enabled(state, selected_rover, selected_order)
    if isinstance(command, StartDay):
        return state.phase is GamePhase.DAY_START
    if isinstance(command, NextDay):
        return state.phase is GamePhase.DAY_END
    return isinstance(
        command,
        (SelectOrder, Pause, ToggleOrders),
    )


def button_selected(button: Button, selected_order_id: str | None) -> bool:
    if isinstance(button.command, SelectOrder):
        return button.command.order_id == selected_order_id
    return False


def overlay_title(state: GameState) -> str:
    if state.phase is GamePhase.DAY_START:
        return "Day start"
    return "Orders"


def overlay_reason(
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
) -> str:
    if selected_rover is None:
        return "Select a rover"
    if selected_order is None:
        return "Select an order"
    result = can_assign(state, selected_rover, selected_order)
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


def rover_card_rect(overlay: pygame.Rect, order_count: int) -> pygame.Rect:
    y = _rows_bottom(overlay, order_count) + ROVER_CARD_GAP
    return pygame.Rect(
        overlay.x + OVERLAY_PAD,
        y,
        overlay.width - 2 * OVERLAY_PAD,
        ROVER_CARD_HEIGHT,
    )


def _hud_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    running = state.phase is GamePhase.RUNNING
    buttons = [_orders_toggle_button(window_size, shift_for_pause=running)]
    if running:
        buttons.append(_pause_button(state, window_size))
    return buttons


def _overlay_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    overlay = overlay_rect(window_size)
    buttons = _order_rows(state, overlay)
    close_index = 2 if state.phase is GamePhase.DAY_START else 1
    buttons.append(_close_button(overlay, close_index))
    if state.phase is GamePhase.DAY_START:
        buttons.append(_start_day_button(overlay))
    buttons.append(_send_button(overlay))
    return buttons


def _order_rows(state: GameState, overlay: pygame.Rect) -> list[Button]:
    buttons: list[Button] = []
    for index, order in enumerate(state.orders):
        buttons.append(
            Button(
                id=f"order-{order.id}",
                rect=_order_row_rect(overlay, index),
                label=_order_label(order),
                command=SelectOrder(order.id),
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


def _close_button(overlay: pygame.Rect, index_from_right: int) -> Button:
    return Button(
        id="close",
        rect=_overlay_action_rect(overlay, index_from_right),
        label="Close",
        command=ToggleOrders(),
    )


def _next_day_button(window_size: tuple[int, int]) -> Button:
    overlay = overlay_rect(window_size)
    return Button(
        id="next-day",
        rect=_overlay_action_rect(overlay, 0),
        label="Next day",
        command=NextDay(),
    )


def _orders_toggle_button(
    window_size: tuple[int, int],
    *,
    shift_for_pause: bool,
) -> Button:
    width, height = HUD_BUTTON_SIZE
    x = window_size[0] - HUD_MARGIN - width
    if shift_for_pause:
        x -= BUTTON_GAP + width
    return Button(
        id="orders",
        rect=pygame.Rect(x, HUD_BUTTON_Y, width, height),
        label="Orders",
        command=ToggleOrders(),
    )


def _pause_button(state: GameState, window_size: tuple[int, int]) -> Button:
    width, height = HUD_BUTTON_SIZE
    return Button(
        id="pause",
        rect=pygame.Rect(
            window_size[0] - HUD_MARGIN - width,
            HUD_BUTTON_Y,
            width,
            height,
        ),
        label="Resume" if state.paused else "Pause",
        command=Pause(),
    )


def _send_enabled(
    state: GameState,
    selected_rover: Rover | None,
    selected_order: Order | None,
) -> bool:
    if state.phase not in (GamePhase.DAY_START, GamePhase.RUNNING):
        return False
    if selected_rover is None or selected_order is None:
        return False
    return can_assign(state, selected_rover, selected_order).allowed


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


def _order_row_rect(overlay: pygame.Rect, index: int) -> pygame.Rect:
    y = overlay.y + OVERLAY_PAD + TITLE_HEIGHT + index * (ROW_HEIGHT + ROW_GAP)
    return pygame.Rect(
        overlay.x + OVERLAY_PAD,
        y,
        overlay.width - 2 * OVERLAY_PAD,
        ROW_HEIGHT,
    )


def _rows_bottom(overlay: pygame.Rect, order_count: int) -> int:
    if order_count <= 0:
        return overlay.y + OVERLAY_PAD + TITLE_HEIGHT
    return _order_row_rect(overlay, order_count - 1).bottom


def _order_label(order: Order) -> str:
    return (
        f"{order.name}  {order.endpoint.name}  "
        f"wt {order.weight}  ${order.reward}  {order.status.value}"
    )
