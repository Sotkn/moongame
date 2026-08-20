from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from moon_game.entities import ShopOffer

if TYPE_CHECKING:
    from moon_game.game_state import GameState


@dataclass(frozen=True)
class BuyResult:
    allowed: bool
    reason: str = ""


def can_buy(state: GameState, offer: ShopOffer) -> BuyResult:
    if offer not in state.shop_offers:
        return BuyResult(False, "Offer gone")
    if state.money < offer.price:
        return BuyResult(False, "Not enough money")
    return BuyResult(True)
