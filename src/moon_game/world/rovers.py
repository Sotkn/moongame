from moon_game.entities import Map, Rover


def build_rovers(play_map: Map) -> list[Rover]:
    return [
        Rover(
            id="hauler",
            position=play_map.base,
            speed=140.0,
            image_key="rover",
            capacity=10,
            battery=180.0,
            battery_max=180.0,
        ),
    ]
