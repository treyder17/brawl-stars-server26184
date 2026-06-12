"""
handlers/chat.py — Simple club-chat echo handler.
"""
from colorama           import Fore, Style
from protocol.messages  import MessageID
from protocol.packet    import PacketReader, DataWriter


async def handle_club_chat(session, payload: bytes):
    log    = session.server.log
    reader = PacketReader(payload)

    try:
        message = reader.read_string()
    except Exception:
        message = ""

    player = session.player
    name   = player.get("name", "Brawler") if player else "???"
    log.info(f"  {Fore.CYAN}CHAT{Style.RESET_ALL} <{name}>: {message}")

    # Echo the message back as a club chat delivery
    w = DataWriter()
    w.write_long(player["_id"] if player else 0)
    w.write_string(name)
    w.write_string(message)
    await session.send_packet(MessageID.CLUB_CHAT_OK, w.get_bytes())
