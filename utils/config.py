"""
utils/config.py — Load config.json and apply environment variable overrides.

Environment variables (all optional) — useful for Railway / Docker:
──────────────────────────────────────────────────────────────────
  MONGO_URL            MongoDB connection string  (overrides mongodb.uri)
  MONGO_DB             Database name              (overrides mongodb.database)
  PORT                 TCP port to listen on      (overrides server.port)
  LOG_LEVEL            DEBUG / INFO / WARNING     (overrides log_level)

  BS_STARTING_GEMS     Starting gems for new players   (default: 9999)
  BS_STARTING_GOLD     Starting gold for new players   (default: 99999)
  BS_STARTING_TICKETS  Starting tickets                (default: 50)

  BS_ALL_BRAWLERS      true/false — unlock all brawlers (default: true)
  BS_ALL_SKINS         true/false — unlock all skins    (default: true)
  BS_UNLIMITED_RES     true/false — unlimited resources (default: true)
"""
import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULTS = {
    "server"  : {"host": "0.0.0.0", "port": 9339},
    "mongodb" : {"uri": "mongodb://localhost:27017", "database": "brawlserver"},
    "log_level": "INFO",
    "features": {
        "allow_all_brawlers"   : True,
        "allow_all_skins"      : True,
        "unlimited_resources"  : True,
    },
    "starting_resources": {
        "gems"   : 9999,
        "gold"   : 99999,
        "tickets": 50,
    },
}


def _env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes")


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def load_config() -> dict:
    # ── Read file (create if missing) ────────────────────────────────
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] config.json not found — creating default at {CONFIG_PATH}")
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULTS, f, indent=2)
        cfg = dict(DEFAULTS)
    else:
        with open(CONFIG_PATH) as f:
            try:
                cfg = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[FATAL] config.json is not valid JSON: {e}")
                sys.exit(1)

    # ── Merge defaults for any missing keys ──────────────────────────
    for key, val in DEFAULTS.items():
        if key not in cfg:
            cfg[key] = val
        elif isinstance(val, dict):
            for sub_key, sub_val in val.items():
                cfg[key].setdefault(sub_key, sub_val)

    # ── Apply environment variable overrides ─────────────────────────
    # Server
    cfg["server"]["host"] = "0.0.0.0"   # always bind all interfaces
    cfg["server"]["port"] = _env_int("PORT", cfg["server"]["port"])

    # MongoDB  (MONGO_URL is *also* read directly in utils/db.py,
    #           but we mirror it here so the rest of the code sees it)
    if os.environ.get("MONGO_URL"):
        cfg["mongodb"]["uri"] = os.environ["MONGO_URL"]
    if os.environ.get("MONGO_DB"):
        cfg["mongodb"]["database"] = os.environ["MONGO_DB"]

    # Logging
    if os.environ.get("LOG_LEVEL"):
        cfg["log_level"] = os.environ["LOG_LEVEL"].upper()

    # Starting resources
    sr = cfg.setdefault("starting_resources", {})
    sr["gems"]    = _env_int("BS_STARTING_GEMS",    sr.get("gems",    9999))
    sr["gold"]    = _env_int("BS_STARTING_GOLD",    sr.get("gold",   99999))
    sr["tickets"] = _env_int("BS_STARTING_TICKETS", sr.get("tickets",   50))

    # Feature flags
    ft = cfg.setdefault("features", {})
    ft["allow_all_brawlers"]  = _env_bool("BS_ALL_BRAWLERS", ft.get("allow_all_brawlers", True))
    ft["allow_all_skins"]     = _env_bool("BS_ALL_SKINS",    ft.get("allow_all_skins",    True))
    ft["unlimited_resources"] = _env_bool("BS_UNLIMITED_RES",ft.get("unlimited_resources",True))

    return cfg
