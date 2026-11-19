from threading import Lock
from time import sleep

import pytest

from app.routes import market_overview


@pytest.fixture(autouse=True)
def reset_market_overview_snapshot_cache(monkeypatch):
    """Keep provider snapshot state isolated between independent route tests."""
    monkeypatch.setattr(market_overview, "_snapshot_cache", None)
    monkeypatch.setattr(market_overview, "_snapshot_cache_at", 0.0)


def test_market_overview_fetches_sources_concurrently(monkeypatch):
    state = {"active": 0, "peak": 0}
    lock = Lock()

    def overlap(_value):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
        sleep(0.05)
        with lock:
            state["active"] -= 1

    def fake_index(index):
        overlap(index)
        return {"name": index["name"], "last_price": 100.0, "status": "success"}

    def fake_movers(kind):
        overlap(kind)
        return [{"symbol": kind.upper()}]

    monkeypatch.setattr(market_overview, "fetch_index", fake_index)
    monkeypatch.setattr(market_overview, "fetch_overview_movers", fake_movers)

    result = market_overview.get_market_overview()

    assert state["peak"] > 1
    assert len(result["indices"]) == len(market_overview.SUPPORTED_INDICES)
    assert result["market_movers"]["gainers"] == [{"symbol": "GAINERS"}]
    assert result["market_movers"]["losers"] == [{"symbol": "LOSERS"}]
    assert result["status"] == "success"


def test_market_overview_keeps_successful_sources_when_one_source_fails(monkeypatch):
    def fake_index(index):
        if index["name"] == "SENSEX":
            raise RuntimeError("temporary provider timeout")
        return {"name": index["name"], "last_price": 100.0, "status": "success"}

    monkeypatch.setattr(market_overview, "fetch_index", fake_index)
    monkeypatch.setattr(
        market_overview,
        "fetch_overview_movers",
        lambda kind: [{"symbol": kind.upper()}],
    )

    result = market_overview.get_market_overview()

    assert result["status"] == "partial"
    assert len(result["indices"]) == len(market_overview.SUPPORTED_INDICES) - 1
    assert result["market_movers"]["gainers"] == [{"symbol": "GAINERS"}]
    assert result["market_movers"]["losers"] == [{"symbol": "LOSERS"}]
    assert any(error.get("name") == "SENSEX" for error in result["errors"])


def test_market_overview_returns_up_to_one_hundred_provider_movers(monkeypatch):
    rows = [
        {"symbol": f"STOCK{i}", "ltp": 100 + i, "per_change": 1.0}
        for i in range(125)
    ]
    monkeypatch.setattr(
        market_overview,
        "fetch_movers",
        lambda **kwargs: {"status": True, "data": rows},
    )
    result = market_overview.fetch_overview_movers("gainers")
    assert len(result) == 100
    assert result[0]["symbol"] == "STOCK0"
    assert result[-1]["symbol"] == "STOCK99"
