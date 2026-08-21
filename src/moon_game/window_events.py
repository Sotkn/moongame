from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pygame


class WindowEventKind(Enum):
    QUIT = "quit"
    CLICK = "click"
    SCROLL = "scroll"


@dataclass(frozen=True)
class WindowEvent:
    kind: WindowEventKind
    position: tuple[int, int] | None = None
    delta: int = 0


def poll_window_events() -> list[WindowEvent]:
    events: list[WindowEvent] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            events.append(WindowEvent(WindowEventKind.QUIT))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            events.append(WindowEvent(WindowEventKind.CLICK, event.pos))
        elif event.type == pygame.MOUSEWHEEL:
            events.append(
                WindowEvent(
                    WindowEventKind.SCROLL,
                    pygame.mouse.get_pos(),
                    event.y,
                )
            )
    return events
