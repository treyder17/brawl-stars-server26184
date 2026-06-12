"""
protocol/messages.py — All known message IDs for v26.184.

Client → Server IDs are in the 10000–19999 range.
Server → Client IDs are in the 20000–29999 range.
"""


class MessageID:
    # ── Client → Server ──────────────────────────────────────────────────
    CLIENT_HELLO        = 10100   # Initial handshake
    LOGIN               = 10101   # Login with account credentials
    KEEP_ALIVE          = 10108   # Heartbeat (no payload)
    GET_HOME_DATA       = 14101   # Request main home screen data
    END_CLIENT_TURN     = 14102   # Battle tick / command
    GO_TO_BATTLE        = 14113   # Player enters matchmaking
    BATTLE_END          = 14114   # Client reports battle result
    CLUB_CHAT           = 14715   # Club chat message

    # ── Server → Client ──────────────────────────────────────────────────
    SERVER_HELLO        = 20100   # Response to CLIENT_HELLO
    LOGIN_OK            = 20104   # Login accepted
    LOGIN_FAILED        = 20103   # Login rejected
    KEEP_ALIVE_OK       = 20108   # Heartbeat ack
    HOME_DATA           = 24101   # Full home/profile payload
    BATTLE_DATA         = 24108   # Battle room data
    BATTLE_END_OK       = 24114   # Battle end acknowledged
    CLUB_CHAT_OK        = 24715   # Club chat delivery ack
    OUT_OF_SYNC         = 24115   # Sync mismatch notification
