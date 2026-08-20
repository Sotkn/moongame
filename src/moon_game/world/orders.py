from moon_game.entities import Order
from moon_game.world.endpoints import OUTPOST, RIDGE


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
            id="ore",
            name="Ore",
            endpoint=RIDGE,
            weight=12,
            reward=120,
        ),
    ]
