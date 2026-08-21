from moon_game.entities import Map
from moon_game.geometry import Vec2

BASE = Vec2(700, 400)


def build_map() -> Map:
    return Map(
        id="crater-plain",
        base=BASE,
        image_key="map",
    )
