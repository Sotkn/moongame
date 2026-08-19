from pygame.time import Clock


class FrameClock:
    def __init__(self, fps: int = 60) -> None:
        self._clock = Clock()
        self._fps = fps

    def dt(self) -> float:
        return self._clock.tick(self._fps) / 1000.0
