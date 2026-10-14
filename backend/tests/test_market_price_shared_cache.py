from decimal import Decimal

import pytest

from app.services import market_price


@pytest.fixture(autouse=True)
def clear_shared_cache():
    with market_price._MARKET_PRICE_CACHE_LOCK:
        market_price._MARKET_PRICE_CACHE.clear()
    yield
    with market_price._MARKET_PRICE_CACHE_LOCK:
        market_price._MARKET_PRICE_CACHE.clear()


def test_shared_cache_reuses_recent_quote_across_calls(monkeypatch):
    calls = []
    def fake_fetch(symbol):
        calls.append(symbol)
        return Decimal("123.45")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    assert market_price.get_market_price("RELIANCE") == Decimal("123.45")
    assert market_price.get_market_price(" reliance ") == Decimal("123.45")
    assert calls == ["RELIANCE"]


def test_shared_cache_isolated_by_symbol(monkeypatch):
    calls = []
    def fake_fetch(symbol):
        calls.append(symbol)
        return Decimal("10") if symbol == "RELIANCE" else Decimal("20")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    assert market_price.get_market_price("RELIANCE") == Decimal("10")
    assert market_price.get_market_price("TCS") == Decimal("20")
    assert calls == ["RELIANCE", "TCS"]


def test_shared_cache_disabled_when_ttl_is_zero(monkeypatch):
    calls = []
    def fake_fetch(symbol):
        calls.append(symbol)
        return Decimal("123.45")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 0.0)

    market_price.get_market_price("RELIANCE")
    market_price.get_market_price("RELIANCE")
    assert calls == ["RELIANCE", "RELIANCE"]


def test_shared_cache_expired_quote_is_refetched(monkeypatch):
    calls = []
    clock = [100.0]
    def fake_fetch(symbol):
        calls.append(symbol)
        return Decimal(str(len(calls)))

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)
    monkeypatch.setattr(market_price, "monotonic", lambda: clock[0])

    assert market_price.get_market_price("RELIANCE") == Decimal("1")
    clock[0] += 1.1
    assert market_price.get_market_price("RELIANCE") == Decimal("2")
    assert calls == ["RELIANCE", "RELIANCE"]


def test_shared_cache_does_not_cache_provider_errors(monkeypatch):
    calls = []
    def fake_fetch(symbol):
        calls.append(symbol)
        raise market_price.MarketPriceError("provider unavailable")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    with pytest.raises(market_price.MarketPriceError):
        market_price.get_market_price("RELIANCE")
    with pytest.raises(market_price.MarketPriceError):
        market_price.get_market_price("RELIANCE")
    assert calls == ["RELIANCE", "RELIANCE"]
