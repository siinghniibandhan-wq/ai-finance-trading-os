import json
from datetime import datetime, timezone

import pytest

from app.services import order_flow_feed
from app.services.order_flow_feed import OrderFlowFeedError, get_order_flow_snapshot


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_snapshot_normalizes_futures_contracts_and_strike_oi(monkeypatch):
    now = datetime.now(timezone.utc)
    payload = {
        "status": "success",
        "data": {
            "last_tick_at": now.isoformat(),
            "futures_contracts": [
                {"symbol": "NIFTY", "expiry": "2026-11-26", "price": 25000,
                 "volume": 100, "oi": 1200, "previous_oi": 1000},
            ],
            "option_contracts": [
                {"strike": 25000, "option_type": "CE", "oi": 500},
                {"strike": 25000, "option_type": "PE", "oi": 700},
            ],
        },
    }
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(order_flow_feed, "urlopen", lambda request, timeout: FakeResponse(payload))

    result = get_order_flow_snapshot("NIFTY")

    assert result["futures_contracts"][0]["oi_change"] == {
        "change": 200, "change_pct": 20.0
    }
    assert result["option_oi_by_strike"] == [
        {"strike": 25000.0, "ce_oi": 500.0, "pe_oi": 700.0}
    ]
    assert result["feed"]["status"] == "fresh"
    assert result["historical_oi_included"] is False


def test_snapshot_fails_closed_when_gateway_is_not_configured(monkeypatch):
    monkeypatch.delenv("MSTOCK_GATEWAY_URL", raising=False)
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    with pytest.raises(OrderFlowFeedError, match="not configured"):
        get_order_flow_snapshot()


def test_snapshot_rejects_untrusted_gateway_payload(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(order_flow_feed, "urlopen", lambda request, timeout: FakeResponse({
        "status": "success", "data": {"futures_contracts": "not-a-list", "option_contracts": []}
    }))
    with pytest.raises(OrderFlowFeedError, match="invalid contract collections"):
        get_order_flow_snapshot()


def test_snapshot_rejects_non_object_contract_rows(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(order_flow_feed, "urlopen", lambda request, timeout: FakeResponse({
        "status": "success",
        "data": {
            "last_tick_at": datetime.now(timezone.utc).isoformat(),
            "futures_contracts": [None],
            "option_contracts": [],
        },
    }))
    with pytest.raises(OrderFlowFeedError, match="contract must be an object"):
        get_order_flow_snapshot()


def test_snapshot_uses_existing_mstock_gateway_url(monkeypatch):
    now = datetime.now(timezone.utc)
    payload = {
        "status": "success",
        "data": {
            "last_tick_at": now.isoformat(),
            "futures_contracts": [],
            "option_contracts": [],
        },
    }
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    requested = {}

    def fake_urlopen(request, timeout):
        requested["url"] = request.full_url
        requested["secret"] = request.get_header("X-financial-os-gateway-secret")
        return FakeResponse(payload)

    monkeypatch.setattr(order_flow_feed, "urlopen", fake_urlopen)

    result = get_order_flow_snapshot("NIFTY")

    assert requested["url"] == "http://127.0.0.1:8000/market-stream/snapshot"
    assert requested["secret"] == "test-secret"
    assert result["feed"]["status"] == "fresh"



class FakeTextResponse(FakeResponse):
    def __init__(self, text):
        self.text = text

    def read(self):
        return self.text.encode("utf-8")


def test_snapshot_maps_real_type_a_tokens_using_gateway_instrument_master(monkeypatch):
    monkeypatch.setattr(order_flow_feed, "_instrument_master_cache", {"csv": None, "loaded_at": 0.0, "rows_by_token": {}})
    exchange_time = datetime.now(timezone.utc).replace(microsecond=0)
    type_a_epoch = datetime(1980, 1, 1, tzinfo=timezone.utc)
    exchange_seconds = int((exchange_time - type_a_epoch).total_seconds())
    instrument_master = (
        "instrument_token,exchange_token,tradingsymbol,name,last_price,expiry,strike,"
        "tick_size,lot_size,instrument_type,segment,exchange\n"
        "101,101,NIFTY26NOVFUT,NIFTY,25000,2026-11-26,,0.05,25,FUTIDX,NSEFO,NSE\n"
        "102,102,NIFTY26NOV25000CE,NIFTY,110,2026-11-26,25000,0.05,25,OPTIDX,NSEFO,NSE\n"
        "103,103,NIFTY26NOV25000PE,NIFTY,120,2026-11-26,25000,0.05,25,OPTIDX,NSEFO,NSE\n"
    )
    snapshot = {
        "status": "success",
        "ticks": [
            {"token": 101, "last_price": 25000.0, "volume": 1200,
             "open_interest": 450000, "exchange_timestamp": exchange_seconds,
             "received_at": "2026-11-18T03:00:01+00:00"},
            {"token": 102, "last_price": 110.0, "volume": 300,
             "open_interest": 12000, "exchange_timestamp": exchange_seconds,
             "received_at": "2026-11-18T03:00:01+00:00"},
            {"token": 103, "last_price": 120.0, "volume": 250,
             "open_interest": 14000, "exchange_timestamp": exchange_seconds,
             "received_at": "2026-11-18T03:00:01+00:00"},
            {"token": 999, "last_price": 1.0, "volume": 1,
             "open_interest": 1, "exchange_timestamp": exchange_seconds,
             "received_at": "2026-11-18T03:00:01+00:00"},
        ],
        "stream": {"connected": True, "stale": False, "mode": 3,
                   "cached_instruments": 4, "reconnect_count": 0},
        "read_only": True,
    }
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    requested = []

    def fake_urlopen(request, timeout):
        requested.append((request.full_url, request.get_header("X-financial-os-gateway-secret")))
        if request.full_url.endswith("/instruments"):
            return FakeTextResponse(instrument_master)
        if request.full_url == "http://127.0.0.1:8000/market-stream/snapshot":
            return FakeResponse(snapshot)
        raise AssertionError(f"Unexpected gateway request: {request.full_url}")

    monkeypatch.setattr(order_flow_feed, "urlopen", fake_urlopen)

    result = get_order_flow_snapshot("NIFTY")

    assert result["feed"]["status"] == "fresh"
    assert result["feed"]["last_tick_at"] == exchange_time.isoformat()
    assert result["futures_contracts"] == [{
        "symbol": "NIFTY", "tradingsymbol": "NIFTY26NOVFUT",
        "expiry": "2026-11-26", "price": 25000.0, "volume": 1200.0,
        "oi": 450000.0, "instrument_token": "101",
        "exchange_timestamp": exchange_time.isoformat(),
        "received_at": "2026-11-18T03:00:01+00:00",
    }]
    assert result["option_oi_by_strike"] == [{
        "strike": 25000.0, "ce_oi": 12000.0, "pe_oi": 14000.0,
        "symbol": "NIFTY",
    }]
    assert result["unmapped_tick_count"] == 1
    assert result["price_scaling"] == "Type A decoder already applied the 1/100 divisor; no additional scaling"
    assert all(secret == "test-secret" for _, secret in requested)


def test_snapshot_filters_instrument_master_mapping_by_requested_underlying(monkeypatch):
    monkeypatch.setattr(order_flow_feed, "_instrument_master_cache", {"csv": None, "loaded_at": 0.0, "rows_by_token": {}})
    exchange_time = datetime.now(timezone.utc).replace(microsecond=0)
    exchange_seconds = int((exchange_time - datetime(1980, 1, 1, tzinfo=timezone.utc)).total_seconds())
    instrument_master = (
        "instrument_token,tradingsymbol,name,expiry,strike,instrument_type,segment,exchange\n"
        "201,NIFTY26NOVFUT,NIFTY,2026-11-26,,FUTIDX,NSEFO,NSE\n"
        "202,BANKNIFTY26NOVFUT,BANKNIFTY,2026-11-26,,FUTIDX,NSEFO,NSE\n"
    )
    snapshot = {"status": "success", "ticks": [
        {"token": 201, "last_price": 25000, "volume": 100, "open_interest": 500,
         "exchange_timestamp": exchange_seconds},
        {"token": 202, "last_price": 56000, "volume": 200, "open_interest": 700,
         "exchange_timestamp": exchange_seconds},
    ], "stream": {"connected": True, "stale": False}}
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")

    def fake_urlopen(request, timeout):
        if request.full_url.endswith("/instruments"):
            return FakeTextResponse(instrument_master)
        return FakeResponse(snapshot)

    monkeypatch.setattr(order_flow_feed, "urlopen", fake_urlopen)

    result = get_order_flow_snapshot("NIFTY")

    assert [item["symbol"] for item in result["futures_contracts"]] == ["NIFTY"]
    assert result["futures_contracts"][0]["price"] == 25000



def test_option_oi_aggregation_keeps_underlyings_separate_at_same_strike():
    from app.services.order_flow_data import aggregate_option_oi

    result = aggregate_option_oi([
        {"symbol": "NIFTY", "strike": 25000, "option_type": "CE", "oi": 12000},
        {"symbol": "BANKNIFTY", "strike": 25000, "option_type": "CE", "oi": 7000},
    ])

    assert result == [
        {"symbol": "BANKNIFTY", "strike": 25000.0, "ce_oi": 7000.0, "pe_oi": 0},
        {"symbol": "NIFTY", "strike": 25000.0, "ce_oi": 12000.0, "pe_oi": 0},
    ]
