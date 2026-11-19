import pytest

from app.routes import market_overview


def test_market_overview_reuses_one_snapshot_for_market_and_flow_consumers(monkeypatch):
    calls = {"indices": 0, "movers": []}
    monkeypatch.setattr(market_overview, "_snapshot_cache", None)
    monkeypatch.setattr(market_overview, "_snapshot_cache_at", 0.0)
    monkeypatch.setattr(market_overview, "SUPPORTED_INDICES", [
        {"name": "NIFTY 50", "exchange": "NSE", "symbol": "NIFTY 50"},
    ])

    def fake_index(index):
        calls["indices"] += 1
        return {"name": index["name"], "exchange": "NSE", "last_price": 25000}

    def fake_movers(mover_type):
        calls["movers"].append(mover_type)
        return [{"symbol": "RELIANCE", "percent_change": 1.2}] if mover_type == "gainers" else []

    monkeypatch.setattr(market_overview, "fetch_index", fake_index)
    monkeypatch.setattr(market_overview, "fetch_overview_movers", fake_movers)

    market_payload = market_overview.get_market_overview()
    flow_payload = market_overview.get_market_overview()

    assert market_payload == flow_payload
    assert calls["indices"] == 1
    assert sorted(calls["movers"]) == ["gainers", "losers"]
    assert flow_payload["market_movers"]["gainers"][0]["symbol"] == "RELIANCE"
