"""
server.py — Async TCP server; accepts connections and dispatches packets.
"""
import asyncio
from colorama import Fore, Style
from protocol.packet    import PacketReader, PacketWriter
from protocol.messages  import MessageID
from handlers.login     import handle_client_hello, handle_login
from handlers.home      import handle_keep_alive, handle_get_home_data, send_home_state
from handlers.battle    import handle_go_to_battle, handle_battle_end
from handlers.chat      import handle_club_chat


class ClientSession:
    """Represents one connected game client."""

    def __init__(self, reader, writer, server):
        self.reader  = reader
        self.writer  = writer
        self.server  = server
        self.addr    = writer.get_extra_info("peername")
        self.player  = None       # loaded from DB after login
        self.account_id: int = 0
        self.authenticated: bool = False

    async def send_packet(self, msg_id: int, payload: bytes):
        pkt = PacketWriter.encode(msg_id, payload)
        self.writer.write(pkt)
        await self.writer.drain()

    def close(self):
        try:
            self.writer.close()
        except Exception:
            pass


class BrawlServer:
    """Top-level server; wires config, DB and game data to each session."""

    # All message IDs the server knows how to handle
    HANDLERS = {
        MessageID.CLIENT_HELLO  : handle_client_hello,
        MessageID.LOGIN         : handle_login,
        MessageID.KEEP_ALIVE    : handle_keep_alive,
        MessageID.GET_HOME_DATA : handle_get_home_data,
        MessageID.GO_TO_BATTLE  : handle_go_to_battle,
        MessageID.BATTLE_END    : handle_battle_end,
        MessageID.CLUB_CHAT     : handle_club_chat,
    }

    def __init__(self, cfg, db, game_data, log):
        self.cfg       = cfg
        self.db        = db
        self.game_data = game_data
        self.log       = log
        self.sessions: dict[str, ClientSession] = {}

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        session = ClientSession(reader, writer, self)
        addr_str = f"{session.addr[0]}:{session.addr[1]}"
        self.sessions[addr_str] = session
        self.log.info(f"{Fore.GREEN}[+] Client connected: {addr_str}{Style.RESET_ALL}")

        try:
            await self._read_loop(session)
        except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError):
            pass
        except Exception as exc:
            self.log.error(f"{Fore.RED}[!] Session error ({addr_str}): {exc}{Style.RESET_ALL}")
        finally:
            session.close()
            self.sessions.pop(addr_str, None)
            self.log.info(f"{Fore.YELLOW}[-] Client disconnected: {addr_str}{Style.RESET_ALL}")

    async def _read_loop(self, session: ClientSession):
        """Continuously read packets and dispatch them."""
        while True:
            # Brawl Stars packet header: 2 bytes ID + 3 bytes length + 2 bytes version
            header = await session.reader.readexactly(7)
            msg_id  = (header[0] << 8) | header[1]
            pay_len = (header[2] << 16) | (header[3] << 8) | header[4]
            # header[5:7] = message version (ignored here)

            payload = b""
            if pay_len > 0:
                payload = await session.reader.readexactly(pay_len)

            self.log.debug(
                f"  ← MSG {msg_id:>5}  len={pay_len:>5}  "
                f"from {session.addr[0]}"
            )

            handler = self.HANDLERS.get(msg_id)
            if handler:
                await handler(session, payload)
            else:
                self.log.debug(f"  [?] Unhandled msg_id={msg_id}")
