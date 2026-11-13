import struct

import pytest

from app.services.mstock_stream import parse_type_a_frame


def _packet(token=1234, ltp=152345, oi=98765, oi_high=100000, oi_low=90000):
    prefix = struct.pack(
        ">16I", token, ltp, 10, 150000, 2500, 100, 120,
        140000, 160000, 130000, 145000, 1700000000,
        oi, oi_high, oi_low, 1700000001,
    )
    return prefix + bytes(120)


def _frame(*packets):
    return struct.pack(">H", len(packets)) + b"".join(
        struct.pack(">H", len(packet)) + packet for packet in packets
    )


def test_parses_full_type_a_packet_and_open_interest():
    ticks = parse_type_a_frame(_frame(_packet()))

    assert len(ticks) == 1
    assert ticks[0]["token"] == 1234
    assert ticks[0]["ltp_raw"] == 152345
    assert ticks[0]["open_interest"] == 98765
    assert ticks[0]["oi_day_high"] == 100000
    assert ticks[0]["oi_day_low"] == 90000
    assert ticks[0]["exchange_timestamp"] == 1700000001


def test_parses_multiple_packets_in_one_frame():
    ticks = parse_type_a_frame(
        _frame(_packet(token=1001), _packet(token=1002, oi=123))
    )

    assert [tick["token"] for tick in ticks] == [1001, 1002]
    assert [tick["open_interest"] for tick in ticks] == [98765, 123]


def test_parses_ltp_and_quote_packets():
    ltp = struct.pack(">2I", 321, 123456)
    quote = struct.pack(">11I", 321, 123456, 4, 123000, 99, 10, 20, 120000, 130000, 110000, 125000)

    ticks = parse_type_a_frame(_frame(ltp, quote))

    assert ticks[0]["token"] == 321
    assert ticks[0]["mode"] == "ltp"
    assert ticks[0]["ltp_raw"] == 123456
    assert ticks[0]["ltp"] == 1234.56
    assert ticks[0]["price_divisor"] == 100
    assert ticks[1]["mode"] == "quote"
    assert ticks[1]["volume"] == 99


def test_ignores_empty_heartbeat_frame():
    assert parse_type_a_frame(b"") == []


@pytest.mark.parametrize("frame", [b"\x00", b"\x00\x01\x00", b"\x00\x01\x00\xb8short"])
def test_rejects_truncated_or_inconsistent_frames(frame):
    with pytest.raises(ValueError):
        parse_type_a_frame(frame)


def test_rejects_unsupported_64_byte_packet():
    with pytest.raises(ValueError):
        parse_type_a_frame(_frame(bytes(64)))


def test_parses_documented_200_byte_full_packet_circuit_and_year_levels():
    packet = _packet() + struct.pack(">4I", 200000, 50000, 250000, 10000)
    ticks = parse_type_a_frame(_frame(packet))
    assert ticks[0]["upper_circuit_raw"] == 200000
    assert ticks[0]["lower_circuit_raw"] == 50000
    assert ticks[0]["year_high_raw"] == 250000
    assert ticks[0]["year_low_raw"] == 10000


def test_normalizes_type_a_prices_using_instrument_segment_divisor_and_1980_epoch():
    packet = struct.pack(
        ">2I", 1234, 152345
    )
    tick = parse_type_a_frame(_frame(packet))[0]
    assert tick["ltp"] == 1523.45
    assert tick["price_divisor"] == 100


def test_normalizes_currency_segment_prices_with_currency_divisor():
    packet = struct.pack(">2I", (1234 << 8) | 3, 1523450000)
    tick = parse_type_a_frame(_frame(packet))[0]
    assert tick["ltp"] == 152.345
    assert tick["price_divisor"] == 10000000


def test_full_tick_exposes_scaled_prices_and_1980_based_exchange_timestamp():
    tick = parse_type_a_frame(_frame(_packet(token=1234, ltp=152345)))[0]
    assert tick["ltp"] == 1523.45
    assert tick["open"] == 1400.0
    assert tick["close"] == 1450.0
    assert tick["exchange_time"] == "2033-11-13T22:13:21+00:00"
    assert tick["bids"][0]["price"] == 0.0
