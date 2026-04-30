# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Decode raw ``Downlink`` MQTT payloads: XOR (team password) + 5-byte frame + Caesar (RF key).

See **docs/guides/decoding-telemetry.md** for the full pipeline. This module implements
enough to recognise **Uplink Intercept** records (``Format = 3``) for cyber / replay scripts.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Crypto (matches docs/guides/encryption-walkthrough.md)
# ---------------------------------------------------------------------------


def xor_crypt(password: str, data: bytes) -> bytes:
    """XOR *data* with UTF-8 *password* (involutive — encrypt and decrypt)."""
    if not data:
        return data
    key = password.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def caesar_decrypt(key: int, data: bytes) -> bytes:
    k = int(key) & 0xFF
    return bytes((b - k) & 0xFF for b in data)


# ---------------------------------------------------------------------------
# Frame peel
# ---------------------------------------------------------------------------

FORMAT_NONE = 0
FORMAT_MESSAGE = 1
FORMAT_MEDIA = 2
FORMAT_UPLINK_INTERCEPT = 3

UPLINK_INTERCEPT_MAGIC_LE = 0x5055495A  # "ZIUP" on wire (LE int32)
INTERCEPT_HEADER_SIZE = 32

# UplinkInterceptRecordFlags (bit order per docs)
FLAG_TRUNCATED = 0x01
FLAG_DECODE_OK = 0x02
FLAG_PARSE_OK = 0x04
FLAG_ADDRESSED_TO_US = 0x08


@dataclass
class PeeledFrame:
    format: int
    team_id: int
    body: bytes


def peel_downlink_frame(xor_decrypted: bytes) -> Optional[PeeledFrame]:
    """
    After XOR, read 1-byte format, 4-byte LE team id, Caesar-decrypt the rest in *a later step*.

    This function expects the **full** XOR-decrypted blob (header + Caesar blob).
    Returns ``None`` if too short.
    """
    if len(xor_decrypted) < 5:
        return None
    fmt = xor_decrypted[0]
    team_id = int.from_bytes(xor_decrypted[1:5], "little")
    body_cipher = xor_decrypted[5:]
    return PeeledFrame(format=fmt, team_id=team_id, body=body_cipher)


def decode_downlink_mqtt_payload(password: str, caesar_key: int, payload: bytes) -> Optional[dict[str, Any]]:
    """
    Full peel: XOR → frame → Caesar → ``{format, team_id, body}``.

    *body* is the inner cleartext (CCSDS packet, media, or intercept record) for *format* 1–3.
    """
    raw = xor_crypt(password, payload)
    if len(raw) < 5:
        return None
    fmt = raw[0]
    team_id = int.from_bytes(raw[1:5], "little")
    body = caesar_decrypt(caesar_key, raw[5:])
    return {"format": fmt, "team_id": team_id, "body": body}


def parse_uplink_intercept_record(body: bytes) -> Optional[dict[str, Any]]:
    """
    Parse *body* as 32-byte header + ``StoredLengthBytes`` wire prefix.

    Returns a dict with ``payload`` (bytes), ``rx_frequency_mhz``, flags, etc., or
    ``None`` if magic/version invalid.
    """
    if len(body) < INTERCEPT_HEADER_SIZE:
        return None
    magic = struct.unpack_from("<i", body, 0)[0]
    if magic != UPLINK_INTERCEPT_MAGIC_LE:
        return None
    version = body[4]
    if version not in (1, 2):
        return None
    sim_time = struct.unpack_from("<d", body, 8)[0]
    wire_len = struct.unpack_from("<i", body, 16)[0]
    stored_len = struct.unpack_from("<i", body, 20)[0]
    flags = body[24]
    rx_mhz: Optional[float] = None
    if version >= 2 and len(body) >= 32:
        rx_mhz = struct.unpack_from("<f", body, 28)[0]
    if stored_len < 0 or stored_len > 4096:
        return None
    end = INTERCEPT_HEADER_SIZE + stored_len
    if len(body) < end:
        return None
    payload = body[INTERCEPT_HEADER_SIZE:end]
    return {
        "version": version,
        "sim_time": sim_time,
        "wire_length": wire_len,
        "stored_length": stored_len,
        "flags": flags,
        "rx_frequency_mhz": rx_mhz,
        "truncated": bool(flags & FLAG_TRUNCATED),
        "decode_ok": bool(flags & FLAG_DECODE_OK),
        "parse_ok": bool(flags & FLAG_PARSE_OK),
        "addressed_to_us": bool(flags & FLAG_ADDRESSED_TO_US),
        "payload": payload,
    }
