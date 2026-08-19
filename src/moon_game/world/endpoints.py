from moon_game.entities import Endpoint
from moon_game.geometry import Vec2

RIDGE = Endpoint(id="ridge", name="Ridge", position=Vec2(840, 120))
CRATER = Endpoint(id="crater", name="Crater", position=Vec2(800, 300))
OUTPOST = Endpoint(id="outpost", name="Outpost", position=Vec2(780, 450))

ENDPOINTS = [RIDGE, CRATER, OUTPOST]
