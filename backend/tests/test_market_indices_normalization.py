import json
from urllib.request import Request

from app.routes import market_indices


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_fetch_index_preserves_change_and_market_timestamp(monkeypatch):
    monkeypatch.setattr(market_indices, "GATEWAY_URL", "http://gateway")
    monkeypatch.setattr(
        market_indices,
        "urlopen",
        lambda request, timeout: FakeResponse({
            "status": "success",
            "data": {
                "NSE:NIFTY 50": {
                    "last_price": "24100.5",
                    "change": "125.5",
                    "per_change": "0.52",
                    "previous_close": "23975",
                    "open": "24000",
                    "high": "24150",
                    "low": "23980",
                    "exchange_timestamp": "2026-11-18T09:20:00+05:30",
                }
            },
        }),
    )

    result = market_indices.fetch_index({
        "name": "NIFTY 50",
        "exchange": "NSE",
        "symbol": "NIFTY 50",
    })

    assert result["last_price"] == 24100.5
    assert result["change"] == 125.5
    assert result["percent_change"] == 0.52
    assert result["previous_close"] == 23975.0
    assert result["open"] == 24000.0
    assert result["high"] == 24150.0
    assert result["low"] == 23980.0
    assert result["market_timestamp"] == "2026-11-18T09:20:00+05:30"


def test_fetch_index_uses_single_nested_quote_when_gateway_key_differs(monkeypatch):
    monkeypatch.setattr(market_indices, "GATEWAY_URL", "http://gateway")
    monkeypatch.setattr(
        market_indices,
        "urlopen",
        lambda request, timeout: FakeResponse({
            "status": "success",
            "data": {
                "NIFTY50": {
                    "last_price": 24000,
                    "change": 100,
                    "percent_change": 0.4,
                }
            },
        }),
    )

    result = market_indices.fetch_index({
        "name": "NIFTY 50",
        "exchange": "NSE",
        "symbol": "NIFTY 50",
    })

    assert result["last_price"] == 24000.0
    assert result["change"] == 100.0
    assert result["percent_change"] == 0.4


def test_fetch_index_does_not_invent_change_when_provider_omits_it(monkeypatch):
    monkeypatch.setattr(market_indices, "GATEWAY_URL", "http://gateway")
    monkeypatch.setattr(
        market_indices,
        "urlopen",
        lambda request, timeout: FakeResponse({
            "status": "success",
            "last_price": 24000,
        }),
    )

    result = market_indices.fetch_index({
        "name": "NIFTY 50",
        "exchange": "NSE",
        "symbol": "NIFTY 50",
    })

    assert result["last_price"] == 24000.0
    assert result["change"] is None
    assert result["percent_change"] is None
