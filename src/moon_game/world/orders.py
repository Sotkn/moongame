from moon_game.entities import Order
from moon_game.world.endpoints import CRATER, OUTPOST, RIDGE


def build_orders() -> list[Order]:
    return [
        Order(
            id="parts",
            name="Parts",
            endpoint=OUTPOST,
            weight=3,
            reward=50,
        ),
        Order(
            id="samples",
            name="Samples",
            endpoint=CRATER,
            weight=6,
            reward=80,
        ),
        Order(
            id="ore",
            name="Ore",
            endpoint=RIDGE,
            weight=20,
            reward=200,
        ),
    ]
