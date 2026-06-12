"""
protocol/packet.py — Low-level packet encode / decode helpers.

Brawl Stars v26.184 wire format
─────────────────────────────────────────────────────
 Offset  Size  Description
  0       2    Message ID  (big-endian uint16)
  2       3    Payload length  (big-endian 24-bit uint)
  5       2    Message version (big-endian uint16)  – usually 0x0000
  7       N    Payload bytes
"""
import struct


class PacketWriter:
    """Build raw packets to send to the client."""

    @staticmethod
    def encode(msg_id: int, payload: bytes, version: int = 0) -> bytes:
        length = len(payload)
        header = struct.pack(
            ">HI",          # 2-byte ID + 4-byte (we extract 3 + 2 below)
            msg_id,
            length & 0xFFFFFF,
        )
        # Rebuild: 2 (ID) + 3 (length) + 2 (version)
        hdr = (
            struct.pack(">H", msg_id)
            + struct.pack(">I", length)[1:]       # drop high byte → 3 bytes
            + struct.pack(">H", version)
        )
        return hdr + payload


class PacketReader:
    """Helpers for reading typed fields from a raw payload bytes."""

    def __init__(self, data: bytes):
        self._buf = data
        self._pos = 0

    # ── Primitives ───────────────────────────────────────────────────────

    def read_byte(self) -> int:
        v = self._buf[self._pos]
        self._pos += 1
        return v

    def read_bool(self) -> bool:
        return bool(self.read_byte())

    def read_int(self) -> int:
        v = struct.unpack(">I", self._buf[self._pos:self._pos+4])[0]
        self._pos += 4
        return v

    def read_short(self) -> int:
        v = struct.unpack(">H", self._buf[self._pos:self._pos+2])[0]
        self._pos += 2
        return v

    def read_long(self) -> int:
        v = struct.unpack(">Q", self._buf[self._pos:self._pos+8])[0]
        self._pos += 8
        return v

    def read_string(self) -> str:
        length = self.read_int()
        if length <= 0:
            return ""
        raw = self._buf[self._pos:self._pos+length]
        self._pos += length
        return raw.decode("utf-8", errors="replace")

    def read_vint(self) -> int:
        """Read a variable-length integer (protobuf-style)."""
        result = 0
        shift  = 0
        while True:
            b = self.read_byte()
            result |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return result

    def read_bytes(self, n: int) -> bytes:
        v = self._buf[self._pos:self._pos+n]
        self._pos += n
        return v

    def remaining(self) -> bytes:
        return self._buf[self._pos:]

    @property
    def pos(self) -> int:
        return self._pos


import struct


class DataWriter:
    """Build a payload byte-by-byte for server → client messages."""

    def __init__(self):
        self._buf = bytearray()

    def write_byte(self, v: int):
        self._buf.append(v & 0xFF)

    def write_bool(self, v: bool):
        self.write_byte(1 if v else 0)

    def write_int(self, v: int):
        self._buf += struct.pack(">I", v & 0xFFFFFFFF)

    def write_short(self, v: int):
        self._buf += struct.pack(">H", v & 0xFFFF)

    def write_long(self, v: int):
        self._buf += struct.pack(">Q", v & 0xFFFFFFFFFFFFFFFF)

    def write_string(self, s: str):
        if s is None:
            self.write_int(0xFFFFFFFF)
            return
        enc = s.encode("utf-8")
        self.write_int(len(enc))
        self._buf += enc

    def write_vint(self, v: int):
        while True:
            byte = v & 0x7F
            v >>= 7
            if v:
                byte |= 0x80
            self._buf.append(byte)
            if not v:
                break

    def write_bytes(self, b: bytes):
        self._buf += b

    def get_bytes(self) -> bytes:
        return bytes(self._buf)
