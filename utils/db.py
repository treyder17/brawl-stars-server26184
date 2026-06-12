"""
utils/db.py — Async MongoDB connection via Motor.

URI priority (highest → lowest):
  1. MONGO_URL  environment variable   ← Railway / production
  2. uri passed in from config.json
  3. Hardcoded fallback mongodb://localhost:27017
"""
import os
import sys
import motor.motor_asyncio

_FALLBACK_URI = "mongodb://localhost:27017"
_client = None


async def connect_db(uri: str, database: str):
    """
    Connect to MongoDB.  The environment variable MONGO_URL always
    takes precedence over whatever is in config.json, so Railway can
    inject the Atlas URI without touching any file.
    """
    global _client

    # Env var wins — lets Railway / docker-compose override config.json
    effective_uri = os.environ.get("MONGO_URL") or uri or _FALLBACK_URI

    # Mask credentials in log output (mongodb+srv://user:PASS@host/…)
    safe_uri = _mask_uri(effective_uri)
    source   = "MONGO_URL env" if os.environ.get("MONGO_URL") else "config.json"

    try:
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            effective_uri,
            serverSelectionTimeoutMS=5000,
        )
        await _client.admin.command("ping")
        return _client[database]
    except Exception as exc:
        print(f"\n[FATAL] Cannot connect to MongoDB!")
        print(f"  Source: {source}")
        print(f"  URI   : {safe_uri}")
        print(f"  Error : {exc}\n")
        print("  → On Railway: set the MONGO_URL environment variable.")
        print("  → Locally   : make sure mongod is running.\n")
        sys.exit(1)


def _mask_uri(uri: str) -> str:
    """Replace password in URI with *** for safe logging."""
    import re
    return re.sub(r"(mongodb(?:\+srv)?://[^:]+:)[^@]+(@)", r"\1***\2", uri)
