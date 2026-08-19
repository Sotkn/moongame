from moon_game.entities import Map, Route
from moon_game.geometry import Vec2
from moon_game.world.endpoints import CRATER, OUTPOST, RIDGE


def build_routes(play_map: Map) -> list[Route]:
    return [
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(380, 220),
                Vec2(620, 280),
            ),
            id="ridge",
            endpoint=RIDGE,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(360, 340),
                Vec2(580, 360),
            ),
            id="crater",
            endpoint=CRATER,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(300, 470),
                Vec2(540, 500),
            ),
            id="outpost",
            endpoint=OUTPOST,
        ),
    ]
