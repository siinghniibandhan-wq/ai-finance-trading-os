from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from time import sleep

import pytest

from app.services import market_price


@pytest.fixture(autouse=True)
def clear_shared_cache():
    with market_price._MARKET_PRICE_CACHE_LOCK:
        market_price._MARKET_PRICE_CACHE.clear()
        market_price._MARKET_PRICE_INFLIGHT.clear()
    yield
    with market_price._MARKET_PRICE_CACHE_LOCK:
        market_price._MARKET_PRICE_CACHE.clear()
        market_price._MARKET_PRICE_INFLIGHT.clear()


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



def test_concurrent_same_symbol_requests_share_one_provider_fetch(monkeypatch):
    calls = []
    start = Barrier(6)

    def fake_fetch(symbol):
        calls.append(symbol)
        sleep(0.05)
        return Decimal("123.45")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    def request_quote():
        start.wait()
        return market_price.get_market_price("RELIANCE")

    with ThreadPoolExecutor(max_workers=6) as executor:
        prices = list(executor.map(lambda _: request_quote(), range(6)))

    assert prices == [Decimal("123.45")] * 6
    assert calls == ["RELIANCE"]


def test_quote_metadata_keeps_original_gateway_retrieval_timestamp_on_cache_hit(monkeypatch):
    calls = []

    def fake_fetch(symbol):
        calls.append(symbol)
        return Decimal("123.45")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    fresh = market_price.get_market_quote("RELIANCE")
    cached = market_price.get_market_quote("RELIANCE")

    assert fresh["cache_hit"] is False
    assert cached["cache_hit"] is True
    assert cached["retrieved_at"] == fresh["retrieved_at"]
    assert calls == ["RELIANCE"]


def test_concurrent_provider_failure_is_shared_without_repeated_gateway_calls(monkeypatch):
    calls = []
    start = Barrier(6)

    def fake_fetch(symbol):
        calls.append(symbol)
        sleep(0.05)
        raise market_price.MarketPriceError("provider unavailable")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    def request_quote():
        start.wait()
        with pytest.raises(market_price.MarketPriceError, match="provider unavailable"):
            market_price.get_market_price("RELIANCE")

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(lambda _: request_quote(), range(6)))

    assert calls == ["RELIANCE"]


def test_unexpected_fetch_error_is_shared_as_market_price_error(monkeypatch):
    calls = []

    def fake_fetch(symbol):
        calls.append(symbol)
        sleep(0.05)
        raise RuntimeError("unexpected transport failure")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)
    start = Barrier(6)

    def request_quote():
        start.wait()
        with pytest.raises(market_price.MarketPriceError, match="Unable to fetch a valid market quote"):
            market_price.get_market_price("RELIANCE")

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(lambda _: request_quote(), range(6)))

    assert calls == ["RELIANCE"]


def test_quote_cache_aliases_unqualified_and_nse_symbol_but_keeps_bse_separate(monkeypatch):
    calls = []

    def fake_fetch(symbol):
        calls.append(symbol)
        return Decimal("200") if symbol.startswith("BSE:") else Decimal("100")

    monkeypatch.setattr(market_price, "_fetch_gateway_quote", fake_fetch)
    monkeypatch.setattr(market_price, "MARKET_PRICE_CACHE_TTL_SECONDS", 1.0)

    assert market_price.get_market_quote("RELIANCE")["price"] == Decimal("100")
    nse_alias = market_price.get_market_quote("NSE:RELIANCE-EQ")
    assert nse_alias["price"] == Decimal("100")
    assert nse_alias["cache_hit"] is True

    bse_quote = market_price.get_market_quote("BSE:RELIANCE")
    assert bse_quote["price"] == Decimal("200")
    assert bse_quote["cache_hit"] is False
    assert calls == ["RELIANCE", "BSE:RELIANCE"]
