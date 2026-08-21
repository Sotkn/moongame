from moon_game.entities import ShopOffer


def build_shop_offers() -> list[ShopOffer]:
    return [
        ShopOffer(
            id="mule",
            name="Мул",
            capacity=20,
            battery_max=160.0,
            speed=140.0,
            image_key="rover",
            price=100,
        ),
        ShopOffer(
            id="dash",
            name="Спринтер",
            capacity=8,
            battery_max=200.0,
            speed=180.0,
            image_key="rover",
            price=150,
        ),
    ]
