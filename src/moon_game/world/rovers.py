from moon_game.entities import Map, Rover


def build_rovers(play_map: Map) -> list[Rover]:
    return [
        Rover(
            id="hauler",
            name="Тягач",
            position=play_map.base,
            speed=140.0,
            image_key="rover",
            capacity=10,
            battery=180.0,
            battery_max=180.0,
        ),
        Rover(
            id="runner",
            name="Бегун",
            position=play_map.base,
            speed=160.0,
            image_key="rover",
            capacity=4,
            battery=95.0,
            battery_max=95.0,
        ),
        Rover(
            id="scout",
            name="Разведчик",
            position=play_map.base,
            speed=120.0,
            image_key="rover",
            capacity=6,
            battery=120.0,
            battery_max=120.0,
        ),
    ]
