from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pygame


class WindowEventKind(Enum):
    QUIT = "quit"
    CLICK = "click"


@dataclass(frozen=True)
class WindowEvent:
    kind: WindowEventKind
    position: tuple[int, int] | None = None


def poll_window_events() -> list[WindowEvent]:
    events: list[WindowEvent] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            events.append(WindowEvent(WindowEventKind.QUIT))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            events.append(WindowEvent(WindowEventKind.CLICK, event.pos))
    return events
