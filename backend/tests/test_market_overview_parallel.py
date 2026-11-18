from threading import Lock
from time import sleep

from app.routes import market_overview


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
