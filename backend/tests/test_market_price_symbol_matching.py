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
