from moon_game.entities import Endpoint
from moon_game.geometry import Vec2

RIDGE = Endpoint(
    id="crater",
    name="Кратер",
    position=Vec2(300, 200),
    image_key="poi1",
)
CRATER = Endpoint(
    id="ridge",
    name="Хребет",
    position=Vec2(1000, 300),
    image_key="poi2",
)
OUTPOST = Endpoint(
    id="outpost",
    name="Форпост",
    position=Vec2(1100, 580),
    image_key="poi3",
)
LAB = Endpoint(
    id="lab",
    name="Лаборатория",
    position=Vec2(169, 512),
    image_key="poi4",
)
DEPOT = Endpoint(
    id="depot",
    name="Склад",
    position=Vec2(623, 571),
    image_key="poi5",
)

ENDPOINTS = [RIDGE, CRATER, OUTPOST, LAB, DEPOT]
