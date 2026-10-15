import json
from decimal import Decimal
from urllib.request import Request

import pytest

from app.services import market_price


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def _mock_gateway(monkeypatch, payload):
    def fake_urlopen(request, timeout):
        assert isinstance(request, Request)
        return FakeResponse(payload)
    monkeypatch.setattr(market_price, "urlopen", fake_urlopen)


def test_quote_uses_exact_requested_symbol(monkeypatch):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "RELIANCE",
        "data": {
            "RELIANCE": {"last_price": "123.45"},
            "TCS": {"last_price": "999.00"},
        },
    })
    assert market_price._fetch_gateway_quote("RELIANCE") == Decimal("123.45")


def test_quote_rejects_ambiguous_multi_symbol_payload(monkeypatch):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "RELIANCE",
        "data": {
            "TCS": {"last_price": "999.00"},
            "INFY": {"last_price": "888.00"},
        },
    })
    with pytest.raises(
        market_price.MarketPriceError,
        match="did not contain an exact quote",
    ):
        market_price._fetch_gateway_quote("RELIANCE")


def test_quote_allows_single_quote_when_gateway_normalizes_key(monkeypatch):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "NSE:RELIANCE-EQ",
        "data": {
            "NSE:RELIANCE-EQ": {"last_price": "123.45"},
        },
    })
    assert market_price._fetch_gateway_quote("RELIANCE") == Decimal("123.45")


@pytest.mark.parametrize("raw_price", ["NaN", "Infinity", "-Infinity", "0", "-1"])
def test_quote_rejects_non_finite_or_non_positive_prices(monkeypatch, raw_price):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "RELIANCE",
        "data": {"RELIANCE": {"last_price": raw_price}},
    })
    with pytest.raises(
        market_price.MarketPriceError,
        match="Invalid market price",
    ):
        market_price._fetch_gateway_quote("RELIANCE")


def test_quote_rejects_single_quote_when_gateway_identifies_a_different_symbol(monkeypatch):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "TCS",
        "data": {"TCS": {"last_price": "999.00"}},
    })
    with pytest.raises(market_price.MarketPriceError, match="while RELIANCE was requested"):
        market_price._fetch_gateway_quote("RELIANCE")


def test_quote_allows_exchange_qualified_symbol_normalization(monkeypatch):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "NSE:RELIANCE-EQ",
        "data": {"RELIANCE-EQ": {"last_price": "123.45"}},
    })
    assert market_price._fetch_gateway_quote("NSE:RELIANCE") == Decimal("123.45")


def test_quote_rejects_non_object_gateway_payload(monkeypatch):
    _mock_gateway(monkeypatch, ["not", "an", "object"])
    with pytest.raises(market_price.MarketPriceError, match="invalid response"):
        market_price._fetch_gateway_quote("RELIANCE")

def test_quote_rejects_non_object_gateway_data(monkeypatch):
    _mock_gateway(monkeypatch, {"status": "success", "symbol": "RELIANCE", "data": []})
    with pytest.raises(market_price.MarketPriceError, match="invalid quote data"):
        market_price._fetch_gateway_quote("RELIANCE")


def test_exchange_qualified_equity_adds_mstock_eq_suffix(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse({
            "status": "success",
            "symbol": "NSE:RELIANCE-EQ",
            "data": {"NSE:RELIANCE-EQ": {"last_price": "123.45"}},
        })

    monkeypatch.setattr(market_price, "urlopen", fake_urlopen)
    assert market_price._fetch_gateway_quote("NSE:RELIANCE") == Decimal("123.45")
    assert "symbol=NSE%3ARELIANCE-EQ" in captured["url"]


def test_market_quote_preserves_year_range_and_trading_metadata(monkeypatch):
    _mock_gateway(monkeypatch, {
        "status": "success",
        "symbol": "NSE:RELIANCE-EQ",
        "data": {
            "NSE:RELIANCE-EQ": {
                "last_price": "123.45",
                "ohlc": {"open": "120", "high": "125", "low": "119", "close": "121"},
                "year_high": "160",
                "year_low": "100",
                "volume_traded_today": "123456",
                "average_traded_price": "122.5",
                "total_buy_qty": "500",
                "total_sell_qty": "450",
                "upper_circuit_limit": "130",
                "lower_circuit_limit": "110",
            },
        },
    })
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 0.0)

    quote = market_price.get_market_quote("NSE:RELIANCE")

    assert quote["price"] == Decimal("123.45")
    assert quote["details"]["open"] == "120"
    assert quote["details"]["high"] == "125"
    assert quote["details"]["previous_close"] == "121"
    assert quote["details"]["year_high"] == "160"
    assert quote["details"]["year_low"] == "100"
    assert quote["details"]["volume"] == "123456"
    assert quote["details"]["average_price"] == "122.5"
    assert quote["details"]["total_buy_quantity"] == "500"
    assert quote["details"]["total_sell_quantity"] == "450"
    assert quote["details"]["upper_circuit_limit"] == "130"
    assert quote["details"]["lower_circuit_limit"] == "110"


def test_exchange_qualified_bse_series_suffix_is_preserved(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse({
            "status": "success",
            "symbol": "BSE:RELIANCE-A",
            "data": {"BSE:RELIANCE-A": {"last_price": "123.45"}},
        })

    monkeypatch.setattr(market_price, "urlopen", fake_urlopen)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 0.0)
    assert market_price._fetch_gateway_quote("BSE:RELIANCE-A") == Decimal("123.45")
    assert "symbol=BSE%3ARELIANCE-A" in captured["url"]
    assert "RELIANCE-A-EQ" not in captured["url"]
