from moon_game.entities import Map, Rover


def build_rovers(play_map: Map) -> list[Rover]:
    return [
        Rover(
            id="rover-1",
            position=play_map.base,
            speed=140.0,
            image_key="rover",
        )
    ]
