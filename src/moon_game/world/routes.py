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
            id="ridge-short",
            name="Short",
            endpoint=RIDGE,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(180, 500),
                Vec2(400, 520),
                Vec2(650, 480),
                Vec2(800, 300),
            ),
            id="ridge-long",
            name="Long",
            endpoint=RIDGE,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(360, 340),
                Vec2(580, 360),
            ),
            id="crater",
            name="Direct",
            endpoint=CRATER,
        ),
        Route.from_waypoints(
            (
                play_map.base,
                Vec2(300, 470),
                Vec2(540, 500),
            ),
            id="outpost",
            name="Direct",
            endpoint=OUTPOST,
        ),
    ]
