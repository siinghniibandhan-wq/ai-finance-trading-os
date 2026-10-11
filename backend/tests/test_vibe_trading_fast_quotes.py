"""Focused tests for Vibe Trading quote cache and batch behavior."""
from decimal import Decimal

from app.routes import vibe_trading


def _clear_cache():
    with vibe_trading.QUOTE_CACHE_LOCK:
        vibe_trading.QUOTE_CACHE.clear()


def test_quote_cache_avoids_repeated_gateway_call(monkeypatch):
    calls = []

    def fake_get_market_price(symbol):
        calls.append(symbol)
        return Decimal("123.45")

    monkeypatch.setattr(vibe_trading, "get_market_price", fake_get_market_price)
    monkeypatch.setattr(vibe_trading, "QUOTE_CACHE_TTL_SECONDS", 2.0)
    _clear_cache()

    first = vibe_trading._quote_result("reliance")
    second = vibe_trading._quote_result("RELIANCE")

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert first["quote"]["last_price"] == 123.45
    assert second["cache_hit"] is True
    assert calls == ["RELIANCE"]


def test_batch_quotes_deduplicates_and_preserves_order(monkeypatch):
    def fake_get_market_price(symbol):
        return Decimal("100.00") if symbol == "TCS" else Decimal("200.00")

    monkeypatch.setattr(vibe_trading, "get_market_price", fake_get_market_price)
    monkeypatch.setattr(vibe_trading, "QUOTE_CACHE_TTL_SECONDS", 0.0)
    _clear_cache()

    result = vibe_trading.vibe_market_quotes(
        vibe_trading.VibeQuotesRequest(symbols=["tcs", "RELIANCE", "TCS"])
    )

    assert result["status"] == "success"
    assert result["count"] == 2
    assert [quote["symbol"] for quote in result["quotes"]] == ["TCS", "RELIANCE"]
    assert [quote["quote"]["last_price"] for quote in result["quotes"]] == [100.0, 200.0]


def test_cache_disabled_when_ttl_zero(monkeypatch):
    calls = []

    def fake_get_market_price(symbol):
        calls.append(symbol)
        return Decimal("42.00")

    monkeypatch.setattr(vibe_trading, "get_market_price", fake_get_market_price)
    monkeypatch.setattr(vibe_trading, "QUOTE_CACHE_TTL_SECONDS", 0.0)
    _clear_cache()

    vibe_trading._quote_result("INFY")
    vibe_trading._quote_result("INFY")

    assert calls == ["INFY", "INFY"]
