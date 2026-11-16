import csv
import io
import json
from datetime import datetime, timezone

import pytest

from app.services import order_flow_gateway_adapter as adapter
from app.services.order_flow_feed import OrderFlowFeedError, get_order_flow_snapshot


MASTER = """instrument_token,tradingsymbol,name,expiry,strike,instrument_type,segment,exchange
101,NIFTY26NOVFUT,NIFTY,2026-11-26,,FUTIDX,NSEFO,NSE
102,NIFTY26NOV25000CE,NIFTY,2026-11-26,25000,OPTIDX,NSEFO,NSE
103,NIFTY26NOV25000PE,NIFTY,2026-11-26,25000,OPTIDX,NSEFO,NSE
104,BANKNIFTY26NOVFUT,BANKNIFTY,2026-11-26,,FUTIDX,NSEFO,NSE
"""


class FakeResponse:
    def __init__(self, body):
        self.body = body.encode() if isinstance(body, str) else body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


@pytest.fixture(autouse=True)
def reset_master_cache():
    adapter._master_cache.update({"loaded_at": 0.0, "rows": None})
    yield
    adapter._master_cache.update({"loaded_at": 0.0, "rows": None})


def test_raw_type_a_ticks_are_joined_to_verified_instrument_metadata():
    master = list(csv.DictReader(io.StringIO(MASTER)))
    now = datetime.now(timezone.utc).timestamp()
    result = adapter.normalize_market_stream(master, [
        {"token": 101, "mode": "full", "ltp_raw": 2500000, "volume": 100,
         "open_interest": 1200, "received_at": now},
        {"token": 102, "mode": "full", "ltp_raw": 5000, "open_interest": 500,
         "received_at": now},
        {"token": 103, "mode": "full", "ltp_raw": 6000, "open_interest": 700,
         "received_at": now},
        {"token": 104, "mode": "full", "ltp_raw": 4000000, "volume": 200,
         "open_interest": 3000, "received_at": now},
    ], "NIFTY")

    assert len(result["futures_contracts"]) == 1
    assert result["futures_contracts"][0]["instrument_token"] == 101
    assert result["futures_contracts"][0]["volume"] == 100
    assert result["futures_contracts"][0]["oi"] == 1200
    assert [(row["option_type"], row["oi"]) for row in result["option_contracts"]] == [
        ("CE", 500), ("PE", 700)
    ]
    assert result["last_tick_at"] is not None


def test_unknown_tokens_and_incomplete_metadata_are_never_guessed():
    result = adapter.normalize_market_stream(
        [{"instrument_token": "1", "name": "NIFTY", "instrument_type": "FUTIDX"}],
        [{"token": 1, "open_interest": 10, "volume": 1, "received_at": 1},
         {"token": 999, "open_interest": 10, "volume": 1, "received_at": 1}],
    )
    assert result["futures_contracts"] == []
    assert result["option_contracts"] == []


def test_underlying_filter_is_applied_from_instrument_master():
    master = list(csv.DictReader(io.StringIO(MASTER)))
    result = adapter.normalize_market_stream(master, [
        {"token": 101, "open_interest": 1200, "volume": 100, "received_at": 1},
        {"token": 104, "open_interest": 3000, "volume": 200, "received_at": 1},
    ], "NIFTY")
    assert [row["symbol"] for row in result["futures_contracts"]] == ["NIFTY"]


def test_gateway_snapshot_uses_existing_raw_stream_and_instrument_master(monkeypatch):
    now = datetime.now(timezone.utc).timestamp()
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.get_header("X-financial-os-gateway-secret"), request.get_method(), request.data))
        if request.full_url.endswith("/instruments"):
            return FakeResponse(MASTER)
        return FakeResponse(json.dumps({
            "status": "success",
            "ticks": [
                {"token": 101, "ltp_raw": 2500000, "volume": 100,
                 "open_interest": 1200, "received_at": now},
                {"token": 102, "ltp_raw": 5000, "open_interest": 500, "received_at": now},
                {"token": 103, "ltp_raw": 6000, "open_interest": 700, "received_at": now},
            ],
            "stream": {"connected": True},
        }))

    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(adapter, "urlopen", fake_urlopen)

    result = get_order_flow_snapshot("NIFTY")

    assert result["feed"]["status"] == "fresh"
    assert len(result["futures_contracts"]) == 1
    assert result["contract_months"][0]["oi"] == 1200
    assert result["option_oi_by_strike"] == [
        {"strike": 25000.0, "ce_oi": 500.0, "pe_oi": 700.0}
    ]
    assert all(secret == "test-secret" for _, secret, _, _ in calls)
    assert any(url.endswith("/market-stream/snapshot") for url, _, _, _ in calls)
    start_calls = [call for call in calls if call[0].endswith("/market-stream/start")]
    assert len(start_calls) == 1
    assert start_calls[0][2] == "POST"
    assert json.loads(start_calls[0][3]) == {"tokens": [101, 102, 103], "mode": 3}


def test_gateway_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(adapter, "_gateway_url", lambda: "")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    with pytest.raises(OrderFlowFeedError, match="URL is not configured"):
        get_order_flow_snapshot()


def test_gateway_authentication_fails_closed(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.delenv("MSTOCK_GATEWAY_SECRET", raising=False)
    with pytest.raises(OrderFlowFeedError, match="authentication is not configured"):
        get_order_flow_snapshot()



def test_gateway_url_requires_explicit_configuration(monkeypatch):
    monkeypatch.delenv("MSTOCK_DERIVATIVES_GATEWAY_URL", raising=False)
    monkeypatch.delenv("MSTOCK_GATEWAY_URL", raising=False)
    assert adapter._gateway_url() == ""


def test_stream_subscription_rejects_more_than_gateway_token_limit():
    master = [
        {"instrument_token": str(token), "name": "NIFTY",
         "expiry": "2026-11-26", "instrument_type": "OPTIDX"}
        for token in range(1, 202)
    ]
    with pytest.raises(OrderFlowFeedError, match="gateway limit is 200"):
        adapter._start_stream("https://gateway.example", master, "NIFTY")
