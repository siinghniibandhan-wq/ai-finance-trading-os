"""Parser for the documented m.Stock Type A binary market-data frames.

This module is intentionally pure: it does not authenticate, connect to a
broker, persist ticks, or place orders. Price fields remain raw provider
integers because the Type A packet documentation specifies field offsets but
does not specify a universal decimal divisor.
"""
from __future__ import annotations

import struct
from typing import Any


_HEADER = struct.Struct(">H")
_PACKET_LENGTH = struct.Struct(">H")
_FULL_PREFIX = struct.Struct(">16I")
_QUOTE_PREFIX = struct.Struct(">11I")


def _parse_packet(packet: memoryview) -> dict[str, Any] | None:
    size = len(packet)
    if size == 8:
        token, ltp = struct.unpack_from(">2I", packet, 0)
        return {"token": token, "mode": "ltp", "ltp_raw": ltp}

    if size == 44:
        values = _QUOTE_PREFIX.unpack_from(packet, 0)
        return {
            "token": values[0],
            "mode": "quote",
            "ltp_raw": values[1],
            "last_traded_quantity": values[2],
            "average_price_raw": values[3],
            "volume": values[4],
            "buy_quantity": values[5],
            "sell_quantity": values[6],
            "open_raw": values[7],
            "high_raw": values[8],
            "low_raw": values[9],
            "close_raw": values[10],
        }

    if size >= 64:
        values = _FULL_PREFIX.unpack_from(packet, 0)
        tick = {
            "token": values[0],
            "mode": "full",
            "ltp_raw": values[1],
            "last_traded_quantity": values[2],
            "average_price_raw": values[3],
            "volume": values[4],
            "buy_quantity": values[5],
            "sell_quantity": values[6],
            "open_raw": values[7],
            "high_raw": values[8],
            "low_raw": values[9],
            "close_raw": values[10],
            "last_trade_timestamp": values[11],
            "open_interest": values[12],
            "oi_day_high": values[13],
            "oi_day_low": values[14],
            "exchange_timestamp": values[15],
        }
        return tick

    raise ValueError(f"Unsupported Type A packet size: {size}")


def parse_type_a_frame(frame: bytes | bytearray | memoryview) -> list[dict[str, Any]]:
    """Decode one Type A WebSocket frame into normalized tick dictionaries.

    Empty frames are treated as heartbeat/no-data frames. The frame header
    contains a big-endian packet count, followed by length-prefixed packets.
    """
    view = memoryview(frame)
    if len(view) == 0:
        return []
    if len(view) < _HEADER.size:
        raise ValueError("Truncated Type A frame header")

    packet_count = _HEADER.unpack_from(view, 0)[0]
    offset = _HEADER.size
    ticks: list[dict[str, Any]] = []

    for _ in range(packet_count):
        if offset + _PACKET_LENGTH.size > len(view):
            raise ValueError("Truncated Type A packet length")
        packet_size = _PACKET_LENGTH.unpack_from(view, offset)[0]
        offset += _PACKET_LENGTH.size
        end = offset + packet_size
        if packet_size <= 0 or end > len(view):
            raise ValueError("Truncated Type A packet payload")
        parsed = _parse_packet(view[offset:end])
        if parsed is not None:
            ticks.append(parsed)
        offset = end

    if offset != len(view):
        raise ValueError("Unexpected trailing bytes in Type A frame")
    return ticks
