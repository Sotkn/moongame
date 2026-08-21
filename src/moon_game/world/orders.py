from moon_game.entities import Order
from moon_game.storage import load_order_rows
from moon_game.world.endpoints import ENDPOINTS

_ENDPOINTS = {endpoint.id: endpoint for endpoint in ENDPOINTS}


def build_orders() -> list[Order]:
    return [
        Order(
            id=row.id,
            name=row.name,
            endpoint=_ENDPOINTS[row.endpoint_id],
            weight=row.weight,
            reward=row.reward,
            deadline=row.deadline,
        )
        for row in load_order_rows()
    ]
