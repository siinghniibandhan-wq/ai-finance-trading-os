from app.routes import market_quote as market_quote_route


def test_market_quote_route_exposes_type_a_ohlc_details(monkeypatch):
    quote_details = {
        "last_price": 1450.25,
        "ohlc": {"open": 1440.0, "high": 1460.0, "low": 1435.0, "close": 1442.0},
        "volume": 123456,
    }
    monkeypatch.setattr(
        market_quote_route,
        "fetch_market_quote",
        lambda _symbol: {
            "price": 1450.25,
            "details": quote_details,
            "retrieved_at": "2026-11-18T10:00:00+00:00",
            "cache_hit": False,
            "cache_age_seconds": 0.0,
            "provider_latency_ms": 12.0,
        },
    )

    response = market_quote_route.get_market_quote("RELIANCE", exchange="NSE")

    assert response["quote"]["last_price"] == 1450.25
    assert response["quote"]["ohlc"] == quote_details["ohlc"]
    assert response["quote"]["volume"] == 123456
