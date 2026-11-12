"""Pure decoder for m.Stock Type A binary market-data frames.

No credentials, network connections, persistence, or order execution live here.
Price values remain raw integers until instrument-specific scaling is resolved.
"""
from __future__ import annotations

import struct
from typing import Any


_HEADER = struct.Struct(">H")
_PACKET_LENGTH = struct.Struct(">H")
_FULL_PREFIX = struct.Struct(">16I")
_QUOTE_PREFIX = struct.Struct(">11I")
_INDEX_QUOTE = struct.Struct(">7I")
_INDEX_FULL = struct.Struct(">8I")


def _parse_packet(packet: memoryview) -> dict[str, Any]:
    size = len(packet)

    if size == 8:
        token, ltp = struct.unpack_from(">2I", packet)
        return {"token": token, "mode": "ltp", "ltp_raw": ltp}

    if size == 28:
        values = _INDEX_QUOTE.unpack_from(packet)
        return {
            "token": values[0], "mode": "index_quote",
            "ltp_raw": values[1], "high_raw": values[2],
            "low_raw": values[3], "open_raw": values[4],
            "close_raw": values[5], "change_raw": values[6],
        }

    if size == 32:
        values = _INDEX_FULL.unpack_from(packet)
        return {
            "token": values[0], "mode": "index_full",
            "ltp_raw": values[1], "high_raw": values[2],
            "low_raw": values[3], "open_raw": values[4],
            "close_raw": values[5], "change_raw": values[6],
            "exchange_timestamp": values[7],
        }

    if size == 44:
        values = _QUOTE_PREFIX.unpack_from(packet)
        return {
            "token": values[0], "mode": "quote",
            "ltp_raw": values[1], "last_traded_quantity": values[2],
            "average_price_raw": values[3], "volume": values[4],
            "buy_quantity": values[5], "sell_quantity": values[6],
            "open_raw": values[7], "high_raw": values[8],
            "low_raw": values[9], "close_raw": values[10],
        }

    # The documented full tradable-instrument packet is 184 bytes:
    # 64-byte quote/OI prefix followed by 120 bytes of five-level depth.
    if size == 184:
        values = _FULL_PREFIX.unpack_from(packet)
        bids = []
        asks = []
        for level in range(5):
            offset = 64 + level * 12
            bids.append({
                "quantity": struct.unpack_from(">I", packet, offset)[0],
                "price_raw": struct.unpack_from(">I", packet, offset + 4)[0],
                "orders": struct.unpack_from(">H", packet, offset + 8)[0],
            })
        for level in range(5):
            offset = 124 + level * 12
            asks.append({
                "quantity": struct.unpack_from(">I", packet, offset)[0],
                "price_raw": struct.unpack_from(">I", packet, offset + 4)[0],
                "orders": struct.unpack_from(">H", packet, offset + 8)[0],
            })
        return {
            "token": values[0], "mode": "full",
            "ltp_raw": values[1], "last_traded_quantity": values[2],
            "average_price_raw": values[3], "volume": values[4],
            "buy_quantity": values[5], "sell_quantity": values[6],
            "open_raw": values[7], "high_raw": values[8],
            "low_raw": values[9], "close_raw": values[10],
            "last_trade_timestamp": values[11],
            "open_interest": values[12], "oi_day_high": values[13],
            "oi_day_low": values[14], "exchange_timestamp": values[15],
            "bids": bids, "asks": asks,
        }

    raise ValueError(f"Unsupported Type A packet size: {size}")


def parse_type_a_frame(frame: bytes | bytearray | memoryview) -> list[dict[str, Any]]:
    """Decode one length-prefixed Type A frame; empty frames are heartbeats."""
    view = memoryview(frame)
    if not view:
        return []
    if len(view) < _HEADER.size:
        raise ValueError("Truncated Type A frame header")

    count = _HEADER.unpack_from(view, 0)[0]
    offset = _HEADER.size
    ticks = []

    for _ in range(count):
        if offset + _PACKET_LENGTH.size > len(view):
            raise ValueError("Truncated Type A packet length")
        packet_size = _PACKET_LENGTH.unpack_from(view, offset)[0]
        offset += _PACKET_LENGTH.size
        end = offset + packet_size
        if packet_size <= 0 or end > len(view):
            raise ValueError("Truncated Type A packet payload")
        ticks.append(_parse_packet(view[offset:end]))
        offset = end

    if offset != len(view):
        raise ValueError("Unexpected trailing bytes in Type A frame")
    return ticks
