"""
handlers/battle.py — GO_TO_BATTLE (14113) and BATTLE_END (14114).

For a local single-player setup we immediately send back a solo room
so the client can start playing offline.  The battle-end updates
trophies and win-counts in the player document.
"""
import time

from colorama           import Fore, Style
from protocol.messages  import MessageID
from protocol.packet    import PacketReader, DataWriter
from models.player      import save_player


async def handle_go_to_battle(session, payload: bytes):
    """Client wants to enter a match. Send BATTLE_DATA to start a room."""
    log    = session.server.log
    reader = PacketReader(payload)

    try:
        slot     = reader.read_int()   # event slot the client selected
        map_id   = reader.read_int()
        mode_id  = reader.read_int()
    except Exception:
        slot, map_id, mode_id = 0, 0, 0

    log.info(
        f"  {Fore.CYAN}GO_TO_BATTLE{Style.RESET_ALL} "
        f"slot={slot} map={map_id} mode={mode_id}"
    )

    # ── Build BATTLE_DATA ─────────────────────────────────────────────
    player = session.player
    w = DataWriter()
    w.write_int(int(time.time()))           # battle start timestamp
    w.write_int(slot)                       # echo slot
    w.write_int(map_id)
    w.write_int(mode_id)
    w.write_long(player["_id"])             # player account id
    w.write_string(player.get("name", "Brawler"))

    # Brawler the player has selected (use first unlocked if none set)
    unlocked = player.get("brawlers", [])
    selected_id = player.get("selected_brawler", 0)
    if not selected_id and unlocked:
        selected_id = unlocked[0].get("id", 16000000)
    w.write_int(selected_id)
    w.write_int(player.get("selected_skin", 0))
    w.write_int(1)      # team id (solo = 1)

    await session.send_packet(MessageID.BATTLE_DATA, w.get_bytes())
    log.info(f"  {Fore.GREEN}→ BATTLE_DATA sent{Style.RESET_ALL}")


async def handle_battle_end(session, payload: bytes):
    """
    Client reports the battle result.
    Update trophy count and win counters.
    """
    log    = session.server.log
    reader = PacketReader(payload)

    try:
        result      = reader.read_int()    # 0=loss, 1=win, 2=draw
        trophies    = reader.read_int()    # trophies gained/lost
        mode_id     = reader.read_int()
    except Exception:
        result, trophies, mode_id = 0, 0, 0

    player = session.player
    log.info(
        f"  {Fore.CYAN}BATTLE_END{Style.RESET_ALL} "
        f"result={result} trophies_delta={trophies:+d}"
    )

    # Apply result to player stats
    if result == 1:
        mode_type = mode_id % 10  # rough guess: 0=3v3, 1=solo, 2=duo
        if mode_type == 1:
            player["solo_wins"] = player.get("solo_wins", 0) + 1
        elif mode_type == 2:
            player["duo_wins"]  = player.get("duo_wins",  0) + 1
        else:
            player["trio_wins"] = player.get("trio_wins", 0) + 1

    player["trophies"] = max(0, player.get("trophies", 0) + trophies)
    if player["trophies"] > player.get("highest_trophies", 0):
        player["highest_trophies"] = player["trophies"]

    await save_player(session.server.db, player)

    # ── Acknowledge ───────────────────────────────────────────────────
    w = DataWriter()
    w.write_int(result)
    w.write_int(player["trophies"])
    await session.send_packet(MessageID.BATTLE_END_OK, w.get_bytes())
    log.info(f"  {Fore.GREEN}→ BATTLE_END_OK sent  (trophies={player['trophies']}){Style.RESET_ALL}")
