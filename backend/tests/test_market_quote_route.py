from app.routes import market_quote as market_quote_route


def test_market_quote_route_calls_service_without_recursing(monkeypatch):
    expected = {
        "price": 123.45,
        "retrieved_at": "2026-10-14T10:00:00+00:00",
        "cache_hit": False,
    }
    calls = []

    def fake_fetch_market_quote(symbol):
        calls.append(symbol)
        return expected

    monkeypatch.setattr(market_quote_route, "fetch_market_quote", fake_fetch_market_quote)
    response = market_quote_route.get_market_quote(" reliance ", exchange="NSE")

    assert calls == ["NSE:RELIANCE"]
    assert response["symbol"] == "RELIANCE"
    assert response["quote"]["last_price"] == 123.45
    assert response["retrieved_at"] == expected["retrieved_at"]
    assert response["cache_hit"] is False


def test_market_quote_route_uses_requested_exchange(monkeypatch):
    calls = []
    monkeypatch.setattr(
        market_quote_route,
        "fetch_market_quote",
        lambda symbol: calls.append(symbol) or {
            "price": 99,
            "retrieved_at": "2026-10-14T10:00:00+00:00",
            "cache_hit": False,
        },
    )

    response = market_quote_route.get_market_quote("RELIANCE", exchange="BSE")

    assert calls == ["BSE:RELIANCE"]
    assert response["exchange"] == "BSE"


def test_market_quote_route_rejects_exchange_conflict(monkeypatch):
    from fastapi import HTTPException
    import pytest

    called = []
    monkeypatch.setattr(
        market_quote_route,
        "fetch_market_quote",
        lambda symbol: called.append(symbol),
    )
    with pytest.raises(HTTPException) as exc:
        market_quote_route.get_market_quote("BSE:RELIANCE", exchange="NSE")
    assert exc.value.status_code == 400
    assert called == []
