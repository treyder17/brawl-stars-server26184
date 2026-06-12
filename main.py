#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   Brawl Stars v26.184 — Local Server Emulator        ║
║   For personal use with a patched Android client     ║
╚══════════════════════════════════════════════════════╝
"""

import os
import sys
import socket
import asyncio

# ── Bootstrap: install requirements if missing ──────────────────────────
def _bootstrap():
    """Auto-install requirements on first run (local dev only)."""
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        return
    try:
        import colorama, pymongo, motor  # noqa: F401
    except ImportError:
        import subprocess
        print("[*] First run — installing requirements …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file, "-q"])
        print("[*] Done. Restarting …\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

_bootstrap()

# ── Imports (all guaranteed after bootstrap) ────────────────────────────
import colorama
from colorama import Fore, Style
colorama.init(autoreset=True)

from utils.config  import load_config
from utils.logger  import setup_logger, banner
from utils.db      import connect_db
from utils.loader  import load_game_data
from server        import BrawlServer

# ── Main ────────────────────────────────────────────────────────────────
async def main():
    banner()

    cfg = load_config()
    log = setup_logger(cfg.get("log_level", "INFO"))

    # ── Resolve host / port ──────────────────────────────────────────
    # PORT env var is set automatically by Railway; we also accept it
    # locally for convenience.  config.json is the fallback.
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", cfg["server"]["port"]))

    log.info(f"{Fore.CYAN}Configuration{Style.RESET_ALL}")
    log.info(f"  Bind     : {Fore.YELLOW}{host}:{port}{Style.RESET_ALL}"
             + (f"  {Fore.CYAN}(from $PORT){Style.RESET_ALL}" if os.environ.get("PORT") else ""))
    log.info(f"  Version  : {Fore.YELLOW}26.184{Style.RESET_ALL}")
    log.info(f"  Log level: {Fore.YELLOW}{cfg.get('log_level','INFO')}{Style.RESET_ALL}")

    # ── MongoDB ──────────────────────────────────────────────────────
    log.info(f"{Fore.CYAN}Connecting to MongoDB …{Style.RESET_ALL}")
    if os.environ.get("MONGO_URL"):
        log.info(f"  Source: {Fore.CYAN}$MONGO_URL env var{Style.RESET_ALL}")
    else:
        log.info(f"  Source: {Fore.CYAN}config.json{Style.RESET_ALL}")

    db = await connect_db(cfg["mongodb"]["uri"], cfg["mongodb"]["database"])
    log.info(f"{Fore.GREEN}✔ MongoDB connected  (db: {cfg['mongodb']['database']}){Style.RESET_ALL}")

    # ── Game data ────────────────────────────────────────────────────
    log.info(f"{Fore.CYAN}Loading game data …{Style.RESET_ALL}")
    game_data = load_game_data()
    log.info(f"{Fore.GREEN}✔ Events  : {len(game_data['events'])} loaded{Style.RESET_ALL}")
    log.info(f"{Fore.GREEN}✔ Shop    : {len(game_data['shop'])} offers loaded{Style.RESET_ALL}")
    log.info(f"{Fore.GREEN}✔ Brawlers: {len(game_data['brawlers'])} loaded{Style.RESET_ALL}")

    # ── Starting resources (env-overridable) ─────────────────────────
    sr = cfg.get("starting_resources", {})
    log.info(
        f"  New players start with: "
        f"{Fore.YELLOW}{sr.get('gems',9999)}{Style.RESET_ALL} gems · "
        f"{Fore.YELLOW}{sr.get('gold',99999)}{Style.RESET_ALL} gold · "
        f"{Fore.YELLOW}{sr.get('tickets',50)}{Style.RESET_ALL} tickets"
    )

    # ── TCP server ───────────────────────────────────────────────────
    srv    = BrawlServer(cfg, db, game_data, log)
    server = await asyncio.start_server(srv.handle_client, host, port)

    # ── Startup banner ───────────────────────────────────────────────
    local_ip   = _get_local_ip()
    on_railway = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"))
    print()
    print(f"{Fore.GREEN}{'═'*56}")
    print(f"{Fore.GREEN}  SERVER IS UP AND RUNNING!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═'*56}{Style.RESET_ALL}")
    if on_railway:
        railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
        print(f"  {Fore.WHITE}Deployed on Railway{Style.RESET_ALL}")
        if railway_url:
            print(f"  {Fore.WHITE}Public TCP host: {Fore.YELLOW}{railway_url}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}Internal port  : {Fore.YELLOW}{port}{Style.RESET_ALL}")
        print()
        print(f"  {Fore.CYAN}→ In Railway dashboard: Settings → Networking → TCP Proxy")
        print(f"  {Fore.CYAN}  Copy the public host:port and use it in libcb.config.so")
    else:
        print(f"  {Fore.WHITE}Local  (same device) : {Fore.YELLOW}127.0.0.1:{port}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}Network (Android/PC) : {Fore.YELLOW}{local_ip}:{port}{Style.RESET_ALL}")
        print()
        print(f"  {Fore.CYAN}→ Patch libcb.config.so with your IP, then start the APK.")
    print(f"{Fore.GREEN}{'═'*56}{Style.RESET_ALL}")
    print()

    async with server:
        await server.serve_forever()


def _get_local_ip() -> str:
    """Best-effort local LAN IP detection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Server stopped by user.{Style.RESET_ALL}")
