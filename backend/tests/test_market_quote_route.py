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
    response = market_quote_route.get_market_quote(" reliance ")

    assert calls == ["RELIANCE"]
    assert response["symbol"] == "RELIANCE"
    assert response["quote"]["last_price"] == 123.45
    assert response["retrieved_at"] == expected["retrieved_at"]
    assert response["cache_hit"] is False
