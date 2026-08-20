from random import Random

from moon_game.entities import Route

HIGH_RISK = 0.5
HAZARD_AT = 0.5
HAZARD_DELAY = 3.0
HAZARD_ENERGY = 20.0


def risk_label(route: Route) -> str:
    return "High" if route.risk >= HIGH_RISK else "Low"


def roll_hazard(route: Route, rng: Random) -> bool:
    return rng.random() < route.risk
