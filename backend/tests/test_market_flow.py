import pytest
from fastapi import HTTPException

from app.routes import market_flow


def _overview(status="success"):
    return {
        "status": status,
        "indices": [{"name": "NIFTY 50", "exchange": "NSE", "last_price": 25281.75}],
        "market_movers": {
            "gainers": [
                {"symbol": "RELIANCE", "name": "Reliance Industries", "exchange": "NSE",
                 "ltp": 1450.5, "percent_change": 1.25, "volume": 1200},
            ],
            "losers": [
                {"symbol": "PAYTM", "name": "One 97 Communications", "exchange": "NSE",
                 "ltp": 350.0, "percent_change": -2.5, "volume": 900},
            ],
        },
        "data_sources": {"primary": "m.Stock via Financial OS Gateway"},
        "errors": [],
        "last_updated": "2026-11-19T04:30:00+00:00",
    }


def test_chart_flow_reuses_the_working_market_overview_feed(monkeypatch):
    calls = []
    monkeypatch.setattr(market_flow, "get_market_overview", lambda: calls.append(True) or _overview())

    result = market_flow.get_market_flow_snapshot()

    assert calls == [True]
    assert result["status"] == "success"
    assert result["indices"][0]["last_price"] == 25281.75
    assert result["market_movers"]["gainers"][0]["symbol"] == "RELIANCE"
    assert result["market_movers"]["losers"][0]["symbol"] == "PAYTM"
    assert result["market_summary"]["gainers"] == 1
    assert result["market_summary"]["losers"] == 1
    assert result["capabilities"]["full_advance_decline_breadth"] is False


def test_chart_flow_preserves_partial_market_overview_data(monkeypatch):
    monkeypatch.setattr(market_flow, "get_market_overview", lambda: _overview("partial"))
    result = market_flow.get_market_flow_snapshot()
    assert result["status"] == "partial"
    assert result["market_movers"]["gainers"][0]["ltp"] == 1450.5


def test_chart_flow_returns_502_when_working_market_feed_has_no_data(monkeypatch):
    payload = _overview("error")
    payload["indices"] = []
    payload["market_movers"] = {"gainers": [], "losers": []}
    monkeypatch.setattr(market_flow, "get_market_overview", lambda: payload)
    with pytest.raises(HTTPException) as exc:
        market_flow.get_market_flow_snapshot()
    assert exc.value.status_code == 502
