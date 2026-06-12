"""
handlers/login.py — CLIENT_HELLO (10100) and LOGIN (10101) handlers.

Handshake flow
──────────────
  Client  →  CLIENT_HELLO  (10100)   contains client version + nonce
  Server  ←  SERVER_HELLO  (20100)   our random nonce, no crypto needed
                                      for a local patched client
  Client  →  LOGIN         (10101)   account_id + pass_token + device info
  Server  ←  LOGIN_OK      (20104)   server fingerprint + account id
"""
import time
import os

from colorama           import Fore, Style
from protocol.messages  import MessageID
from protocol.packet    import PacketReader, DataWriter
from models.player      import load_or_create_player, save_player


async def handle_client_hello(session, payload: bytes):
    """
    Respond to CLIENT_HELLO.
    Payload contains the client version and a client nonce; we reply
    with SERVER_HELLO which sends back our own nonce.
    """
    log = session.server.log

    # Parse client hello (version + 24-byte nonce)
    reader = PacketReader(payload)
    try:
        client_version = reader.read_int()
        nonce = reader.read_bytes(24)
    except Exception:
        client_version = 0
        nonce = b"\x00" * 24

    log.info(
        f"  {Fore.CYAN}CLIENT_HELLO{Style.RESET_ALL} "
        f"client_version={client_version} "
        f"from {session.addr[0]}"
    )

    # Build SERVER_HELLO payload:
    #   server_version (4) + server_nonce (24) + server_random (24)
    writer = DataWriter()
    writer.write_int(client_version)          # echo version back
    writer.write_bytes(os.urandom(24))        # server nonce (no crypto needed)
    writer.write_bytes(os.urandom(24))        # padding / server random

    await session.send_packet(MessageID.SERVER_HELLO, writer.get_bytes())
    log.info(f"  {Fore.GREEN}→ SERVER_HELLO sent{Style.RESET_ALL}")


async def handle_login(session, payload: bytes):
    """
    Handle LOGIN from client. Load or create a player document in MongoDB,
    then respond with LOGIN_OK.
    """
    log = session.server.log

    reader = PacketReader(payload)
    try:
        account_id    = reader.read_long()
        pass_token    = reader.read_string()
        client_major  = reader.read_int()
        client_minor  = reader.read_int()
        fingerprint   = reader.read_string()
        _device_id    = reader.read_string()
        _locale       = reader.read_string()
        device_model  = reader.read_string()
    except Exception as exc:
        log.warning(f"  [!] Malformed LOGIN packet: {exc}")
        account_id   = 0
        pass_token   = "anon"
        device_model = "Unknown"

    log.info(
        f"  {Fore.CYAN}LOGIN{Style.RESET_ALL} "
        f"account_id={account_id} "
        f"device='{device_model}' "
        f"v{client_major}.{client_minor}"
    )

    # ── Load / create player ──────────────────────────────────────────
    db          = session.server.db
    starting_res = session.server.cfg.get("starting_resources", {})
    player = await load_or_create_player(db, account_id, pass_token, starting_res)

    session.player       = player
    session.account_id   = player["_id"]
    session.authenticated = True

    # ── Build LOGIN_OK ────────────────────────────────────────────────
    w = DataWriter()
    w.write_long(player["_id"])                    # assigned account id
    w.write_string(player["pass_token"])           # echo pass token
    w.write_string("prod.brawlstarsgame.com")      # server host (informational)
    w.write_string("")                             # facebook id (empty)
    w.write_string("en")                           # content language
    w.write_string("")                             # region
    w.write_string("26.184")                       # server version string
    w.write_string("")                             # update URL (none)
    w.write_int(0)                                 # reason (0 = OK)

    await session.send_packet(MessageID.LOGIN_OK, w.get_bytes())
    log.info(
        f"  {Fore.GREEN}→ LOGIN_OK sent  "
        f"(player '{player.get('name', 'Unnamed')}'  "
        f"id={player['_id']}){Style.RESET_ALL}"
    )

    # Immediately push home data so the menu loads
    from handlers.home import send_home_state
    await send_home_state(session)
