from moon_game.entities import Map, Route
from moon_game.geometry import Vec2
from moon_game.world.endpoints import CRATER, OUTPOST, RIDGE


def build_routes(play_map: Map) -> list[Route]:
    return [
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(540, 244),
            ),
            id="ridge-short",
            name="Короткий",
            endpoint=RIDGE,
            risk=0.7,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(480, 590),
                Vec2(130, 610),
                Vec2(45, 450),
                Vec2(120, 270),
            ),
            id="ridge-long",
            name="Длинный",
            endpoint=RIDGE,
            risk=0.1,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(900, 240),
            ),
            id="crater",
            name="Прямой",
            endpoint=CRATER,
            risk=0.1,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(764, 584),
            ),
            id="outpost",
            name="Прямой",
            endpoint=OUTPOST,
            risk=0.1,
        ),
    ]
