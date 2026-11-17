import json
from datetime import datetime, timezone, timedelta

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
    monkeypatch.setenv("MSTOCK_DERIVATIVES_GATEWAY_URL", "https://gateway.example")
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
    monkeypatch.delenv("MSTOCK_DERIVATIVES_GATEWAY_URL", raising=False)
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    with pytest.raises(OrderFlowFeedError, match="not configured"):
        get_order_flow_snapshot()


def test_snapshot_rejects_untrusted_gateway_payload(monkeypatch):
    monkeypatch.setenv("MSTOCK_DERIVATIVES_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(order_flow_feed, "urlopen", lambda request, timeout: FakeResponse({
        "status": "success", "data": {"futures_contracts": "not-a-list", "option_contracts": []}
    }))
    with pytest.raises(OrderFlowFeedError, match="invalid contract collections"):
        get_order_flow_snapshot()


def _live_payload(**data_extra):
    now = datetime.now(timezone.utc)
    data = {
        "last_tick_at": now.isoformat(),
        "futures_contracts": [
            {"symbol": "NIFTY", "expiry": "2026-11-26", "price": 25000,
             "volume": 100, "oi": 1200, "previous_oi": None},
        ],
        "option_contracts": [
            {"strike": 25000, "option_type": "CE", "oi": 500},
            {"strike": 25000, "option_type": "PE", "oi": 700},
        ],
    }
    data.update(data_extra)
    return {"status": "success", "data": data}


def _configure(monkeypatch, payload):
    monkeypatch.setenv("MSTOCK_DERIVATIVES_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(order_flow_feed, "urlopen", lambda request, timeout: FakeResponse(payload))


def test_snapshot_passes_coverage_and_stream_through(monkeypatch):
    coverage = {"state": "ready", "futures_planned": 2, "futures_with_data": 1,
                "options_planned": 42, "options_with_data": 2,
                "unavailable": [{"tradingsymbol": "NIFTY26DECFUT", "reason": "no tick received"}]}
    stream = {"running": True, "authenticated": True, "login_state": "authenticated",
              "login_confirmed_by": "first_tick", "last_error": None}
    _configure(monkeypatch, _live_payload(coverage=coverage, stream=stream))

    result = get_order_flow_snapshot("NIFTY")

    assert result["coverage"] == coverage
    assert result["stream"] == stream


def test_snapshot_coverage_and_stream_are_none_when_gateway_omits_them(monkeypatch):
    _configure(monkeypatch, _live_payload())

    result = get_order_flow_snapshot()

    assert result["coverage"] is None
    assert result["stream"] is None


def test_snapshot_existing_keys_unchanged_by_coverage_passthrough(monkeypatch):
    payload = _live_payload(coverage={"state": "ready"}, stream={"running": True})
    _configure(monkeypatch, payload)

    result = get_order_flow_snapshot("NIFTY")

    assert set(result) == {
        "status", "source", "read_only", "as_of", "feed", "futures_contracts",
        "contract_months", "option_oi_by_strike", "historical_oi_included",
        "coverage", "stream",
    }
    assert result["status"] == "success"
    assert result["read_only"] is True
    assert result["as_of"] == payload["data"]["last_tick_at"]
    assert result["feed"]["status"] == "fresh"
    assert result["historical_oi_included"] is False
    assert result["option_oi_by_strike"] == [
        {"strike": 25000.0, "ce_oi": 500.0, "pe_oi": 700.0}
    ]
    # previous_oi is null, so no change is invented.
    assert "oi_change" not in result["futures_contracts"][0]
