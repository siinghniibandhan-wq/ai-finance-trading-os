import json
import time

import pytest

from app.services import order_flow_feed
from app.services.order_flow_feed import OrderFlowFeedError, get_order_flow_snapshot


INSTRUMENTS_CSV = """exchange,tradingsymbol,name,instrument_token,segment,instrument_type,expiry,strike,lot_size
NFO,NIFTY26NOVFUT,NIFTY,101,FUTIDX,,2026-11-26,,75
NFO,NIFTY26NOV25000CE,NIFTY,102,OPTIDX,CE,2026-11-26,25000,75
NFO,NIFTY26NOV25000PE,NIFTY,103,OPTIDX,PE,2026-11-26,25000,75
NFO,BANKNIFTY26NOVFUT,BANKNIFTY,104,FUTIDX,,2026-11-26,,30
"""


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        if isinstance(self.payload, str):
            return self.payload.encode("utf-8")
        return json.dumps(self.payload).encode("utf-8")


def configure_gateway(monkeypatch, snapshot):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://gateway.example:8000")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")

    calls = []
    monkeypatch.setattr(order_flow_feed, "_INSTRUMENT_CACHE", {"loaded_at": 0.0, "items": None})

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        if request.full_url.endswith("/instruments"):
            return FakeResponse(INSTRUMENTS_CSV)
        if request.full_url.endswith("/market-stream/start"):
            return FakeResponse({"status": "success", "started": True, "read_only": True})
        if "/market-stream/snapshot" in request.full_url:
            return FakeResponse(snapshot)
        raise AssertionError(f"Unexpected gateway URL: {request.full_url}")

    monkeypatch.setattr(order_flow_feed, "urlopen", fake_urlopen)
    return calls


def test_snapshot_adapts_production_market_stream_ticks_using_instrument_master(monkeypatch):
    now = time.time()
    snapshot = {
        "status": "success",
        "ticks": [
            {"instrument_token": 101, "token": 101, "last_price": 25012.5,
             "volume_traded": 1200, "oi": 450000, "exchange_timestamp": "2026-11-18T09:20:00+05:30"},
            {"instrument_token": 102, "token": 102, "last_price": 125.5,
             "volume_traded": 100, "oi": 12000},
            {"instrument_token": 103, "token": 103, "last_price": 130.0,
             "volume_traded": 150, "oi": 14000},
            {"instrument_token": 104, "token": 104, "last_price": 56000.0,
             "volume_traded": 500, "oi": 80000},
        ],
        "stream": {
            "running": True,
            "connected": True,
            "socket_connected": True,
            "stream_verified": True,
            "stale": False,
            "last_tick_at": now,
            "cached_instruments": 4,
            "reconnect_count": 0,
            "mode": 3,
        },
        "read_only": True,
    }
    calls = configure_gateway(monkeypatch, snapshot)

    result = get_order_flow_snapshot("NIFTY")

    assert result["status"] == "success"
    assert result["source"] == "m.Stock via Financial OS market-stream gateway"
    assert result["read_only"] is True
    future = result["futures_contracts"][0]
    assert {
        "symbol": future["symbol"],
        "tradingsymbol": future["tradingsymbol"],
        "exchange": future["exchange"],
        "expiry": future["expiry"],
        "price": future["price"],
        "volume": future["volume"],
        "oi": future["oi"],
        "instrument_token": future["instrument_token"],
    } == {
        "symbol": "NIFTY",
        "tradingsymbol": "NIFTY26NOVFUT",
        "exchange": "NFO",
        "expiry": "2026-11-26",
        "price": 25012.5,
        "volume": 1200,
        "oi": 450000,
        "instrument_token": 101,
    }
    assert result["option_oi_by_strike"] == [
        {"strike": 25000.0, "ce_oi": 12000.0, "pe_oi": 14000.0}
    ]
    assert result["feed"]["status"] == "fresh"
    assert result["stream"]["connected"] is True
    assert "previous_oi" not in result["futures_contracts"][0]
    assert "oi_change" not in result["futures_contracts"][0]
    assert len(calls) == 3
    start_request = next(req for req, _ in calls if req.full_url.endswith("/market-stream/start"))
    assert start_request.get_method() == "POST"
    start_payload = json.loads(start_request.data.decode("utf-8"))
    assert start_payload["mode"] == 3
    assert set(start_payload["tokens"]) == {101, 102, 103}
    snapshot_request = next(req for req, _ in calls if "/market-stream/snapshot" in req.full_url)
    assert next(value for key, value in snapshot_request.header_items()
                if key.lower() == "x-financial-os-gateway-secret") == "test-secret"


def test_snapshot_uses_shared_market_gateway_configuration(monkeypatch):
    configure_gateway(monkeypatch, {
        "status": "success", "ticks": [],
        "stream": {"running": False, "connected": False, "stream_verified": False,
                   "last_tick_at": None, "stale": True},
    })
    monkeypatch.delenv("MSTOCK_DERIVATIVES_GATEWAY_URL", raising=False)

    result = get_order_flow_snapshot()

    assert result["feed"]["status"] == "disconnected"
    assert result["futures_contracts"] == []
    assert result["option_oi_by_strike"] == []


def test_snapshot_fails_closed_when_gateway_or_secret_is_not_configured(monkeypatch):
    monkeypatch.delenv("MSTOCK_GATEWAY_URL", raising=False)
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    with pytest.raises(OrderFlowFeedError, match="gateway is not configured"):
        get_order_flow_snapshot()

    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://gateway.example")
    monkeypatch.delenv("MSTOCK_GATEWAY_SECRET", raising=False)
    with pytest.raises(OrderFlowFeedError, match="authentication is not configured"):
        get_order_flow_snapshot()


def test_snapshot_rejects_gateway_errors_and_invalid_payloads(monkeypatch):
    configure_gateway(monkeypatch, {"status": "error", "ticks": [], "stream": {}})
    with pytest.raises(OrderFlowFeedError, match="successful market-stream snapshot"):
        get_order_flow_snapshot()

    configure_gateway(monkeypatch, {"status": "success", "ticks": "invalid", "stream": {}})
    with pytest.raises(OrderFlowFeedError, match="invalid tick collection"):
        get_order_flow_snapshot()


def test_snapshot_does_not_claim_live_when_stream_is_stale_or_has_no_ticks(monkeypatch):
    configure_gateway(monkeypatch, {
        "status": "success",
        "ticks": [{"instrument_token": 101, "last_price": 25000, "volume_traded": 1, "oi": 2}],
        "stream": {
            "running": True, "connected": False, "stream_verified": False,
            "stale": True, "last_tick_at": time.time() - 120,
        },
    })

    result = get_order_flow_snapshot()

    assert result["feed"]["status"] == "stale"
    assert result["stream"]["connected"] is False

    configure_gateway(monkeypatch, {
        "status": "success", "ticks": [],
        "stream": {"running": True, "connected": False, "stream_verified": False,
                   "stale": True, "last_tick_at": None},
    })
    result = get_order_flow_snapshot()
    assert result["feed"]["status"] == "disconnected"


def test_snapshot_rejects_ticks_without_verified_instrument_metadata(monkeypatch):
    configure_gateway(monkeypatch, {
        "status": "success",
        "ticks": [{"instrument_token": 999999, "last_price": 100, "oi": 10}],
        "stream": {"last_tick_at": time.time(), "connected": True, "stream_verified": True},
    })

    result = get_order_flow_snapshot()

    assert result["futures_contracts"] == []
    assert result["option_oi_by_strike"] == []
    assert result["coverage"]["unmapped_ticks"] == 1
