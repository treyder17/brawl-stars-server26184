#!/usr/bin/env python3
"""
tools/admin.py — Simple command-line admin panel.

Usage
─────
  python tools/admin.py list                        List all players
  python tools/admin.py show  <account_id>          Show one player
  python tools/admin.py gems  <account_id> <amount>  Set gem count
  python tools/admin.py gold  <account_id> <amount>  Set gold count
  python tools/admin.py name  <account_id> <name>    Rename player
  python tools/admin.py reset <account_id>           Reset to defaults
"""
import sys
import asyncio
import json
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.config import load_config
from utils.db     import connect_db


async def _get_col():
    cfg = load_config()
    db  = await connect_db(cfg["mongodb"]["uri"], cfg["mongodb"]["database"])
    return db["players"]


async def cmd_list():
    col = await _get_col()
    docs = await col.find({}, {"name": 1, "trophies": 1, "gems": 1}).to_list(100)
    if not docs:
        print("No players found.")
        return
    print(f"\n{'ID':>15}  {'Name':20}  {'Trophies':>8}  {'Gems':>6}")
    print("─" * 60)
    for d in docs:
        print(f"{d['_id']:>15}  {d.get('name','?'):20}  {d.get('trophies',0):>8}  {d.get('gems',0):>6}")
    print()


async def cmd_show(account_id: int):
    col = await _get_col()
    doc = await col.find_one({"_id": account_id})
    if not doc:
        print(f"Player {account_id} not found.")
        return
    # Pretty print without brawler list (too long)
    short = {k: v for k, v in doc.items() if k != "brawlers"}
    print(json.dumps(short, indent=2, default=str))
    print(f"  Brawlers: {len(doc.get('brawlers',[]))} unlocked")


async def cmd_set_field(account_id: int, field: str, value):
    col = await _get_col()
    res = await col.update_one({"_id": account_id}, {"$set": {field: value}})
    if res.matched_count:
        print(f"  ✔ {field} = {value} for player {account_id}")
    else:
        print(f"  Player {account_id} not found.")


async def cmd_reset(account_id: int):
    from models.player import _default_brawlers
    col = await _get_col()
    updates = {
        "gems": 9999, "gold": 99999, "trophies": 0,
        "brawlers": _default_brawlers(),
    }
    res = await col.update_one({"_id": account_id}, {"$set": updates})
    if res.matched_count:
        print(f"  ✔ Player {account_id} reset to defaults.")
    else:
        print(f"  Player {account_id} not found.")


async def _main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()

    if cmd == "list":
        await cmd_list()
    elif cmd == "show" and len(args) >= 2:
        await cmd_show(int(args[1]))
    elif cmd == "gems" and len(args) >= 3:
        await cmd_set_field(int(args[1]), "gems", int(args[2]))
    elif cmd == "gold" and len(args) >= 3:
        await cmd_set_field(int(args[1]), "gold", int(args[2]))
    elif cmd == "name" and len(args) >= 3:
        await cmd_set_field(int(args[1]), "name", args[2])
    elif cmd == "reset" and len(args) >= 2:
        await cmd_reset(int(args[1]))
    else:
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(_main())
