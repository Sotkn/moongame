from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

_FILES = {
    "map": "map.jpg",
    "rover": "rover1.png",
    "base": "base.png",
    "poi1": "poi1.png",
    "poi2": "poi2.png",
    "poi3": "poi3.png",
    "poi4": "poi4.png",
    "poi5": "poi5.png",
}


def asset_path(key: str) -> Path:
    return _ASSETS_DIR / _FILES[key]
