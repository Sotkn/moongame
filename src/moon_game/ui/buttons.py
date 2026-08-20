from __future__ import annotations

from dataclasses import dataclass

import pygame

from moon_game.assignment import can_assign
from moon_game.entities import Order, Rover
from moon_game.game_state import GameState
from moon_game.ui.commands import Confirm, Pause, SelectOrder, SelectRover

CONTROL_ORIGIN = (16, 488)
BUTTON_SIZE = (112, 36)
BUTTON_GAP = 8
PAUSE_SIZE = (112, 36)
PAUSE_MARGIN = 16

type ButtonCommand = SelectOrder | SelectRover | Confirm | Pause


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
    buttons = _order_buttons(state)
    buttons.extend(_rover_buttons(state, len(buttons)))
    buttons.append(_confirm_button(len(buttons)))
    buttons.append(_pause_button(state, window_size))
    return buttons


def button_enabled(
    button: Button,
    state: GameState,
    selected_order: Order | None,
    selected_rover: Rover | None,
) -> bool:
    if isinstance(button.command, Confirm):
        return _confirm_enabled(state, selected_order, selected_rover)
    if isinstance(button.command, Pause):
        return True
    return isinstance(button.command, (SelectOrder, SelectRover))


def button_selected(
    button: Button,
    selected_order: Order | None,
    selected_rover: Rover | None,
) -> bool:
    if isinstance(button.command, SelectOrder):
        return button.command.order is selected_order
    if isinstance(button.command, SelectRover):
        return button.command.rover is selected_rover
    return False


def confirm_reason(
    state: GameState,
    selected_order: Order | None,
    selected_rover: Rover | None,
) -> str:
    if not state.paused:
        return "Pause to assign"
    if selected_order is None or selected_rover is None:
        return "Select an order and a rover"
    result = can_assign(state, selected_rover, selected_order)
    if result.allowed:
        return ""
    return result.reason


def _confirm_enabled(
    state: GameState,
    selected_order: Order | None,
    selected_rover: Rover | None,
) -> bool:
    if not state.paused or selected_order is None or selected_rover is None:
        return False
    return can_assign(state, selected_rover, selected_order).allowed


def _order_buttons(state: GameState) -> list[Button]:
    buttons: list[Button] = []
    x, y = CONTROL_ORIGIN
    width, height = BUTTON_SIZE
    for order in state.orders:
        buttons.append(
            Button(
                id=f"order-{order.id}",
                rect=pygame.Rect(x, y, width, height),
                label=order.name,
                command=SelectOrder(order),
            )
        )
        x += width + BUTTON_GAP
    return buttons


def _rover_buttons(state: GameState, index: int) -> list[Button]:
    buttons: list[Button] = []
    x, y = CONTROL_ORIGIN
    width, height = BUTTON_SIZE
    x += index * (width + BUTTON_GAP)
    for rover in state.rovers:
        buttons.append(
            Button(
                id=f"rover-{rover.id}",
                rect=pygame.Rect(x, y, width, height),
                label=rover.id,
                command=SelectRover(rover),
            )
        )
        x += width + BUTTON_GAP
    return buttons


def _confirm_button(index: int) -> Button:
    x, y = CONTROL_ORIGIN
    width, height = BUTTON_SIZE
    x += index * (width + BUTTON_GAP)
    return Button(
        id="confirm",
        rect=pygame.Rect(x, y, width, height),
        label="Confirm",
        command=Confirm(),
    )


def _pause_button(state: GameState, window_size: tuple[int, int]) -> Button:
    width, height = PAUSE_SIZE
    return Button(
        id="pause",
        rect=pygame.Rect(
            window_size[0] - PAUSE_MARGIN - width,
            CONTROL_ORIGIN[1],
            width,
            height,
        ),
        label="Resume" if state.paused else "Pause",
        command=Pause(),
    )
