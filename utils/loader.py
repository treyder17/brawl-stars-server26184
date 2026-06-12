"""
utils/loader.py — Load game data JSON files at startup.

Files are intentionally kept separate so you can edit them
without touching any Python code.
"""
import json
import os


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_json(rel_path: str) -> list:
    full = os.path.join(DATA_DIR, rel_path)
    if not os.path.exists(full):
        return []
    with open(full) as f:
        return json.load(f)


def load_game_data() -> dict:
    return {
        "events"  : _load_json("events/events.json"),
        "shop"    : _load_json("shop/shop.json"),
        "brawlers": _load_json("brawlers/brawlers.json"),
    }
