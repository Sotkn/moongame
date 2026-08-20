from moon_game.entities import Order
from moon_game.world.day import DAY_LENGTH
from moon_game.world.endpoints import CRATER, RIDGE


def build_orders() -> list[Order]:
    return [
        Order(
            id="mail",
            name="Mail",
            endpoint=RIDGE,
            weight=3,
            reward=50,
            deadline=13.0,
        ),
        Order(
            id="tools",
            name="Tools",
            endpoint=RIDGE,
            weight=8,
            reward=80,
            deadline=DAY_LENGTH,
        ),
        Order(
            id="samples",
            name="Samples",
            endpoint=CRATER,
            weight=6,
            reward=80,
            deadline=DAY_LENGTH,
        ),
        Order(
            id="ore",
            name="Ore",
            endpoint=RIDGE,
            weight=20,
            reward=200,
            deadline=DAY_LENGTH,
        ),
    ]
