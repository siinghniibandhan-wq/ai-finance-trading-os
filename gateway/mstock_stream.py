"""Minimal shared Type A frame decoder for m.Stock market-data packets."""
import struct


def parse_type_a_frame(frame):
    if not frame:
        return []
    if len(frame) < 2:
        raise ValueError("Truncated Type A frame header")
    count = struct.unpack_from(">H", frame)[0]
    offset = 2
    ticks = []
    for _ in range(count):
        if offset + 2 > len(frame):
            raise ValueError("Truncated Type A packet length")
        size = struct.unpack_from(">H", frame, offset)[0]
        offset += 2
        end = offset + size
        if size <= 0 or end > len(frame):
            raise ValueError("Truncated Type A packet payload")
        packet = memoryview(frame)[offset:end]
        if size == 8:
            token, ltp = struct.unpack_from(">2I", packet)
            tick = {"token": token, "mode": "ltp", "ltp_raw": ltp}
        elif size == 28:
            values = struct.unpack_from(">7I", packet)
            tick = {"token": values[0], "mode": "index_quote", "ltp_raw": values[1],
                    "high_raw": values[2], "low_raw": values[3], "open_raw": values[4],
                    "close_raw": values[5], "change_raw": values[6]}
        elif size == 32:
            values = struct.unpack_from(">8I", packet)
            tick = {"token": values[0], "mode": "index_full", "ltp_raw": values[1],
                    "high_raw": values[2], "low_raw": values[3], "open_raw": values[4],
                    "close_raw": values[5], "change_raw": values[6], "exchange_timestamp": values[7]}
        elif size == 44:
            values = struct.unpack_from(">11I", packet)
            tick = {"token": values[0], "mode": "quote", "ltp_raw": values[1],
                    "last_traded_quantity": values[2], "average_price_raw": values[3],
                    "volume": values[4], "buy_quantity": values[5], "sell_quantity": values[6],
                    "open_raw": values[7], "high_raw": values[8], "low_raw": values[9],
                    "close_raw": values[10]}
        elif size == 184:
            values = struct.unpack_from(">16I", packet)
            tick = {"token": values[0], "mode": "full", "ltp_raw": values[1],
                    "high_raw": values[2], "low_raw": values[3], "open_raw": values[4],
                    "close_raw": values[5], "volume": values[4], "open_interest": values[12],
                    "oi_day_high": values[13], "oi_day_low": values[14],
                    "exchange_timestamp": values[15]}
        else:
            raise ValueError(f"Unsupported Type A packet size: {size}")
        ticks.append(tick)
        offset = end
    if offset != len(frame):
        raise ValueError("Unexpected trailing bytes in Type A frame")
    return ticks
