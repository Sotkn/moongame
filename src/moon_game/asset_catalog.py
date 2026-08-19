from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

_FILES = {
    "map": "map.png",
    "rover": "rover.png",
}


def asset_path(key: str) -> Path:
    return _ASSETS_DIR / _FILES[key]
