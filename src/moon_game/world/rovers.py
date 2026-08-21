from moon_game.entities import Map, Rover
from moon_game.storage import load_rover_rows


def build_rovers(play_map: Map) -> list[Rover]:
    return [
        Rover(
            id=row.id,
            name=row.name,
            position=play_map.base,
            speed=row.speed,
            image_key=row.image_key,
            capacity=row.capacity,
            battery=row.battery_max,
            battery_max=row.battery_max,
        )
        for row in load_rover_rows()
    ]
