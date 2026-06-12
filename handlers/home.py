"""
handlers/home.py — Home data, keep-alive, and home state senders.

HOME_DATA (24101) is the big payload that tells the client about:
  • Player profile  (name, trophies, gems, gold, tickets …)
  • Brawler roster  (unlocked brawlers + star powers + gadgets)
  • Active events   (loaded from data/events/events.json)
  • Shop offers     (loaded from data/shop/shop.json)
  • Alliance / Club data
"""
import time

from colorama           import Fore, Style
from protocol.messages  import MessageID
from protocol.packet    import PacketReader, DataWriter


async def handle_keep_alive(session, payload: bytes):
    await session.send_packet(MessageID.KEEP_ALIVE_OK, b"")
    session.server.log.debug("  ↔ KEEP_ALIVE")


async def handle_get_home_data(session, payload: bytes):
    session.server.log.info(
        f"  {Fore.CYAN}GET_HOME_DATA{Style.RESET_ALL} "
        f"from {session.addr[0]}"
    )
    await send_home_state(session)


async def send_home_state(session):
    """Build and send the full HOME_DATA packet."""
    log        = session.server.log
    player     = session.player
    game_data  = session.server.game_data
    cfg        = session.server.cfg

    w = DataWriter()

    # ── Timestamp ─────────────────────────────────────────────────────
    w.write_int(int(time.time()))

    # ── Player profile ────────────────────────────────────────────────
    w.write_long(player["_id"])
    w.write_string(player.get("name", "Brawler"))
    w.write_int(player.get("trophies", 0))
    w.write_int(player.get("highest_trophies", 0))
    w.write_int(player.get("experience", 0))
    w.write_int(player.get("gems", 0))
    w.write_int(player.get("gold", 0))
    w.write_int(player.get("star_points", 0))
    w.write_int(player.get("tickets", 0))
    w.write_int(player.get("solo_wins", 0))
    w.write_int(player.get("duo_wins", 0))
    w.write_int(player.get("trio_wins", 0))
    w.write_bool(player.get("is_developer", False))

    # ── Brawlers ──────────────────────────────────────────────────────
    unlocked = player.get("brawlers", [])
    w.write_int(len(unlocked))
    for b in unlocked:
        w.write_int(b.get("id", 0))
        w.write_int(b.get("trophies", 0))
        w.write_int(b.get("highest_trophies", 0))
        w.write_int(b.get("power_level", 1))
        w.write_int(b.get("power_points", 0))
        # Star power list
        star_powers = b.get("star_powers", [])
        w.write_int(len(star_powers))
        for sp in star_powers:
            w.write_int(sp)
        # Gadget list
        gadgets = b.get("gadgets", [])
        w.write_int(len(gadgets))
        for g in gadgets:
            w.write_int(g)
        w.write_bool(b.get("selected_skin", 0) != 0)
        w.write_int(b.get("selected_skin", 0))

    # ── Active events ─────────────────────────────────────────────────
    events = game_data.get("events", [])
    w.write_int(len(events))
    for ev in events:
        w.write_int(ev.get("id", 0))
        w.write_int(ev.get("mode_id", 0))
        w.write_int(ev.get("map_id", 0))
        w.write_string(ev.get("map_name", ""))
        w.write_int(ev.get("slot", 0))
        w.write_int(ev.get("start_time", 0))
        w.write_int(ev.get("end_time", 0))
        # event modifiers list
        mods = ev.get("modifiers", [])
        w.write_int(len(mods))
        for m in mods:
            w.write_int(m)

    # ── Shop offers ───────────────────────────────────────────────────
    shop = game_data.get("shop", [])
    w.write_int(len(shop))
    for offer in shop:
        w.write_int(offer.get("id", 0))
        w.write_string(offer.get("name", ""))
        w.write_int(offer.get("cost_gems", 0))
        w.write_int(offer.get("cost_gold", 0))
        w.write_int(offer.get("product_type", 0))
        w.write_int(offer.get("product_id", 0))
        w.write_int(offer.get("product_count", 1))
        w.write_bool(offer.get("is_featured", False))

    # ── Server settings ───────────────────────────────────────────────
    w.write_bool(cfg.get("features", {}).get("allow_all_brawlers", True))
    w.write_bool(cfg.get("features", {}).get("allow_all_skins", True))
    w.write_bool(cfg.get("features", {}).get("unlimited_resources", True))

    await session.send_packet(MessageID.HOME_DATA, w.get_bytes())
    log.info(f"  {Fore.GREEN}→ HOME_DATA sent to {session.addr[0]}{Style.RESET_ALL}")
