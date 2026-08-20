from __future__ import annotations

from dataclasses import dataclass

import pygame

from moon_game.assignment import can_assign
from moon_game.commands import DismissChoice, Pause
from moon_game.entities import ChooseDelivery, Order
from moon_game.game_state import GamePhase, GameState
from moon_game.ui.commands import Confirm, SelectOrder

OVERLAY_SIZE = (700, 440)
OVERLAY_PAD = 24
TITLE_HEIGHT = 32
ROW_HEIGHT = 40
ROW_GAP = 8
ROVER_CARD_GAP = 16
ROVER_CARD_HEIGHT = 72
BUTTON_SIZE = (140, 40)
BUTTON_GAP = 8
PAUSE_SIZE = (112, 36)
PAUSE_MARGIN = 16
PAUSE_Y = 488

type ButtonCommand = SelectOrder | Confirm | DismissChoice | Pause


@dataclass
class Button:
    id: str
    rect: pygame.Rect
    label: str
    command: ButtonCommand


def build_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    if state.overlay_open():
        return _overlay_buttons(state, window_size)
    return [_pause_button(state, window_size)]


def button_enabled(
    button: Button,
    state: GameState,
    selected_order: Order | None,
) -> bool:
    if isinstance(button.command, Confirm):
        return _commit_enabled(state, selected_order)
    return isinstance(
        button.command,
        (SelectOrder, DismissChoice, Pause),
    )


def button_selected(button: Button, selected_order: Order | None) -> bool:
    if isinstance(button.command, SelectOrder):
        return button.command.order is selected_order
    return False


def overlay_title(state: GameState) -> str:
    if state.phase is GamePhase.DAY_START:
        return "Day start"
    return "Choose delivery"


def overlay_reason(state: GameState, selected_order: Order | None) -> str:
    if selected_order is None:
        return "Select an order"
    result = can_assign(state, state.day_rover(), selected_order)
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


def _overlay_buttons(
    state: GameState,
    window_size: tuple[int, int],
) -> list[Button]:
    overlay = overlay_rect(window_size)
    buttons = _order_rows(state, overlay)
    buttons.append(_commit_button(state, overlay))
    if isinstance(state.pending_event, ChooseDelivery):
        buttons.append(_done_button(overlay))
    return buttons


def _order_rows(state: GameState, overlay: pygame.Rect) -> list[Button]:
    buttons: list[Button] = []
    for index, order in enumerate(state.orders):
        buttons.append(
            Button(
                id=f"order-{order.id}",
                rect=_order_row_rect(overlay, index),
                label=_order_label(order),
                command=SelectOrder(order),
            )
        )
    return buttons


def _commit_button(state: GameState, overlay: pygame.Rect) -> Button:
    width, height = BUTTON_SIZE
    return Button(
        id="commit",
        rect=pygame.Rect(
            overlay.right - OVERLAY_PAD - width,
            overlay.bottom - OVERLAY_PAD - height,
            width,
            height,
        ),
        label="Start day" if state.phase is GamePhase.DAY_START else "Send",
        command=Confirm(),
    )


def _done_button(overlay: pygame.Rect) -> Button:
    width, height = BUTTON_SIZE
    return Button(
        id="done",
        rect=pygame.Rect(
            overlay.right - OVERLAY_PAD - 2 * width - BUTTON_GAP,
            overlay.bottom - OVERLAY_PAD - height,
            width,
            height,
        ),
        label="Done",
        command=DismissChoice(),
    )


def _pause_button(state: GameState, window_size: tuple[int, int]) -> Button:
    width, height = PAUSE_SIZE
    return Button(
        id="pause",
        rect=pygame.Rect(
            window_size[0] - PAUSE_MARGIN - width,
            PAUSE_Y,
            width,
            height,
        ),
        label="Resume" if state.paused else "Pause",
        command=Pause(),
    )


def _commit_enabled(state: GameState, selected_order: Order | None) -> bool:
    if selected_order is None:
        return False
    return can_assign(state, state.day_rover(), selected_order).allowed


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
