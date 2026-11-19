import json
from contextlib import contextmanager

import pytest

from app.routes import market_indices


class FakeResponse:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode()


@pytest.mark.parametrize("price", ["NaN", "Infinity", 0, -1, "not-a-number"])
def test_index_quote_rejects_invalid_prices(monkeypatch, price):
    monkeypatch.setattr(market_indices, "urlopen", lambda *args, **kwargs: FakeResponse({"status": "success", "last_price": price}))
    with pytest.raises(ValueError):
        market_indices.fetch_index({"name": "NIFTY 50", "exchange": "NSE", "symbol": "NIFTY 50"})


def test_index_quote_accepts_positive_finite_price(monkeypatch):
    monkeypatch.setattr(market_indices, "urlopen", lambda *args, **kwargs: FakeResponse({"status": "success", "last_price": "24500.5"}))
    result = market_indices.fetch_index({"name": "NIFTY 50", "exchange": "NSE", "symbol": "NIFTY 50"})
    assert result["last_price"] == 24500.5


def test_index_quote_derives_change_only_from_provider_ohlc_close(monkeypatch):
    monkeypatch.setattr(market_indices, "urlopen", lambda *args, **kwargs: FakeResponse({
        "status": "success",
        "data": {
            "NSE:NIFTY IT": {
                "last_price": "35000",
                "ohlc": {"open": "34800", "high": "35100", "low": "34750", "close": "34750"},
            }
        },
    }))
    result = market_indices.fetch_index({
        "name": "NIFTY IT", "exchange": "NSE", "symbol": "NIFTY IT",
    })
    assert result["last_price"] == 35000
    assert result["previous_close"] == 34750
    assert result["change"] == 250
    assert result["percent_change"] == pytest.approx(250 / 34750 * 100)


def test_index_quote_leaves_change_unavailable_without_provider_previous_close(monkeypatch):
    monkeypatch.setattr(market_indices, "urlopen", lambda *args, **kwargs: FakeResponse({
        "status": "success", "last_price": "35000",
    }))
    result = market_indices.fetch_index({
        "name": "NIFTY IT", "exchange": "NSE", "symbol": "NIFTY IT",
    })
    assert result["last_price"] == 35000
    assert result["previous_close"] is None
    assert result["change"] is None
    assert result["percent_change"] is None
