from __future__ import annotations

from dataclasses import dataclass

import pygame

from moon_game.game_state import GamePhase, GameState
from moon_game.ui.commands import Pause, PlayerCommand, StartRoute

LAUNCH_SIZE = (168, 40)
LAUNCH_ORIGIN = (24, 480)
LAUNCH_GAP = 12
PAUSE_SIZE = (160, 40)
PAUSE_MARGIN = 24


@dataclass
class Button:
    id: str
    rect: pygame.Rect
    label: str
    command: PlayerCommand


def build_buttons(state: GameState, window_size: tuple[int, int]) -> list[Button]:
    buttons = _launch_buttons(state)
    buttons.append(_pause_button(state, window_size))
    return buttons


def button_enabled(button: Button, state: GameState) -> bool:
    if isinstance(button.command, StartRoute):
        return state.phase is GamePhase.PLANNING
    if isinstance(button.command, Pause):
        return state.phase is GamePhase.EXECUTION
    return False


def _launch_buttons(state: GameState) -> list[Button]:
    buttons: list[Button] = []
    x, y = LAUNCH_ORIGIN
    width, height = LAUNCH_SIZE
    for route in state.routes:
        buttons.append(
            Button(
                id=f"launch-{route.id}",
                rect=pygame.Rect(x, y, width, height),
                label=route.endpoint.name,
                command=StartRoute(route),
            )
        )
        x += width + LAUNCH_GAP
    return buttons


def _pause_button(state: GameState, window_size: tuple[int, int]) -> Button:
    width, height = PAUSE_SIZE
    return Button(
        id="pause",
        rect=pygame.Rect(
            window_size[0] - PAUSE_MARGIN - width,
            LAUNCH_ORIGIN[1],
            width,
            height,
        ),
        label="Resume" if state.paused else "Pause",
        command=Pause(),
    )
