"""
models/player.py — Player document schema and MongoDB helpers.

A player document looks like:
{
  "_id"              : <int account_id>,
  "pass_token"       : "abc123",
  "name"             : "Brawler",
  "trophies"         : 500,
  "highest_trophies" : 500,
  "experience"       : 0,
  "gems"             : 999,
  "gold"             : 10000,
  "star_points"      : 0,
  "tickets"          : 20,
  "solo_wins"        : 0,
  "duo_wins"         : 0,
  "trio_wins"        : 0,
  "is_developer"     : false,
  "selected_brawler" : 16000000,
  "selected_skin"    : 0,
  "brawlers"         : [
      {
        "id": 16000000, "trophies": 0, "highest_trophies": 0,
        "power_level": 9, "power_points": 0,
        "star_powers": [], "gadgets": [], "selected_skin": 0
      },
      ...
  ]
}
"""
import random
import string
import time

COLLECTION = "players"


def _new_account_id() -> int:
    """Generate a random 64-bit account ID."""
    return random.randint(10_000_000_000, 99_999_999_999)


def _new_pass_token(length: int = 40) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def _default_brawlers() -> list:
    """All 26.184 brawlers unlocked at power 9."""
    # Brawl Stars v26.184 brawler IDs (numeric)
    # fmt: off
    ids = [
        16000000,  # Shelly
        16000001,  # Colt
        16000002,  # Bull
        16000003,  # Brock
        16000004,  # Rico
        16000005,  # Spike
        16000006,  # Barley
        16000007,  # Jessie
        16000008,  # Nita
        16000009,  # Dynamike
        16000010,  # El Primo
        16000011,  # Mortis
        16000012,  # Crow
        16000013,  # Poco
        16000014,  # Bo
        16000015,  # Piper
        16000016,  # Pam
        16000017,  # Tara
        16000018,  # Darryl
        16000019,  # Penny
        16000020,  # Frank
        16000021,  # Gene
        16000022,  # Tick
        16000023,  # Leon
        16000024,  # Rosa
        16000025,  # Carl
    ]
    # fmt: on
    return [
        {
            "id"               : bid,
            "trophies"         : 500,
            "highest_trophies" : 500,
            "power_level"      : 9,
            "power_points"     : 0,
            "star_powers"      : [],
            "gadgets"          : [],
            "selected_skin"    : 0,
        }
        for bid in ids
    ]


def _default_player(account_id: int, pass_token: str, starting_res: dict | None = None) -> dict:
    sr = starting_res or {}
    return {
        "_id"              : account_id,
        "pass_token"       : pass_token,
        "name"             : "Brawler",
        "trophies"         : 0,
        "highest_trophies" : 0,
        "experience"       : 0,
        "gems"             : sr.get("gems",    9_999),
        "gold"             : sr.get("gold",   99_999),
        "star_points"      : 0,
        "tickets"          : sr.get("tickets",    50),
        "solo_wins"        : 0,
        "duo_wins"         : 0,
        "trio_wins"        : 0,
        "is_developer"     : False,
        "selected_brawler" : 16000000,
        "selected_skin"    : 0,
        "brawlers"         : _default_brawlers(),
        "created_at"       : int(time.time()),
        "last_login"       : int(time.time()),
    }


async def load_or_create_player(
    db, account_id: int, pass_token: str, starting_res: dict | None = None
) -> dict:
    """
    Load a player by account_id.  If not found, create a fresh document.
    If account_id is 0 (new device) generate one.
    starting_res — dict with gems/gold/tickets for new players (from config).
    """
    col = db[COLLECTION]

    if account_id != 0:
        doc = await col.find_one({"_id": account_id})
        if doc:
            await col.update_one(
                {"_id": account_id},
                {"$set": {"last_login": int(time.time())}}
            )
            doc["last_login"] = int(time.time())
            return doc

    # ── New player ────────────────────────────────────────────────────
    new_id    = _new_account_id()
    new_token = pass_token if pass_token else _new_pass_token()
    player    = _default_player(new_id, new_token, starting_res)
    await col.insert_one(player)
    return player


async def save_player(db, player: dict):
    """Persist updated player document."""
    col = db[COLLECTION]
    await col.replace_one({"_id": player["_id"]}, player, upsert=True)
