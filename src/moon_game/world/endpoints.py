from moon_game.entities import Endpoint
from moon_game.geometry import Vec2

RIDGE = Endpoint(
    id="ridge",
    name="Ridge",
    position=Vec2(300, 200),
    image_key="poi1",
)
CRATER = Endpoint(
    id="crater",
    name="Crater",
    position=Vec2(1000, 300),
    image_key="poi2",
)
OUTPOST = Endpoint(
    id="outpost",
    name="Outpost",
    position=Vec2(1100, 580),
    image_key="poi3",
)

ENDPOINTS = [RIDGE, CRATER, OUTPOST]
