from moon_game.game_state import load_state
from moon_game.session import Session
from moon_game.ui import Ui


def run() -> None:
    ui = Ui()
    try:
        Session(ui, load_state()).run()
    finally:
        ui.close()
