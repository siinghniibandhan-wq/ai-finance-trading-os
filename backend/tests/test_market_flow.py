import pytest
from fastapi import HTTPException

from app.routes import market_flow


def test_chart_flow_requests_all_cash_movers_from_both_exchanges(monkeypatch):
    calls = []
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        exchange = "NSE" if kwargs["exchange"] == 1 else "BSE"
        return {
            "status": True,
            "message": "SUCCESS",
            "data": [{
                "exchange": exchange,
                "symbol": exchange + ("UP" if kwargs["type_flag"] == "G" else "DOWN"),
                "symbol_name": exchange + " sample",
                "ltp": 100,
                "per_change": 1 if kwargs["type_flag"] == "G" else -1,
                "volume": 500,
            }],
        }

    monkeypatch.setattr(market_flow, "fetch_movers", fake_fetch)
    monkeypatch.setattr(market_flow, "fetch_index", lambda index: {
        "name": index["name"], "exchange": index["exchange"], "symbol": index["symbol"],
        "last_price": 100, "status": "success",
    })

    result = market_flow.get_market_flow_snapshot()

    assert len(calls) == 4
    assert all(call["security_id_code"] == 0 for call in calls)
    assert {(call["exchange"], call["segment"]) for call in calls} == {(1, 1), (4, 2)}
    assert {call["type_flag"] for call in calls} == {"G", "L"}
    assert len(result["market_movers"]["gainers"]) == 2
    assert len(result["market_movers"]["losers"]) == 2
    assert result["market_summary"]["unchanged"] is None
    assert result["scope"]["universe"].startswith("ALL cash-market")


def test_chart_flow_marks_partial_provider_failures_without_filling_missing_data(monkeypatch):
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)
    call_count = {"value": 0}

    def fake_fetch(**kwargs):
        call_count["value"] += 1
        if call_count["value"] == 1:
            raise RuntimeError("provider unavailable")
        return {"status": True, "data": []}

    monkeypatch.setattr(market_flow, "fetch_movers", fake_fetch)
    monkeypatch.setattr(market_flow, "fetch_index", lambda index: {
        "name": index["name"], "exchange": index["exchange"], "symbol": index["symbol"],
        "last_price": 100, "status": "success",
    })

    result = market_flow.get_market_flow_snapshot()

    assert result["status"] == "partial"
    assert result["errors"][0]["message"] == "provider unavailable"
    assert result["market_movers"] == {"gainers": [], "losers": []}
    assert result["market_summary"]["unchanged"] is None


def test_chart_flow_returns_502_when_every_source_fails(monkeypatch):
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(market_flow, "fetch_movers", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("movers down")))
    monkeypatch.setattr(market_flow, "fetch_index", lambda _index: (_ for _ in ()).throw(RuntimeError("index down")))

    with pytest.raises(HTTPException) as exc:
        market_flow.get_market_flow_snapshot()

    assert exc.value.status_code == 502
    assert "Unable to retrieve Chart Flow" in exc.value.detail["message"]


def test_chart_flow_sector_movers_uses_mstock_sector_universe(monkeypatch):
    calls = []
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(market_flow, "_sector_cache", {})

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        flag = kwargs["type_flag"]
        return {
            "status": True,
            "data": [{
                "exchange": "NSE",
                "symbol": "INFY" if flag == "G" else "WIPRO",
                "symbol_name": "Infosys" if flag == "G" else "Wipro",
                "ltp": 1500,
                "per_change": 2 if flag == "G" else -1,
                "volume": 1000,
            }],
        }

    monkeypatch.setattr(market_flow, "fetch_movers", fake_fetch)
    monkeypatch.setattr(market_flow, "fetch_index", lambda index: {
        "name": index["name"], "exchange": index["exchange"], "symbol": index["symbol"],
        "last_price": 25000, "status": "success",
    })

    result = market_flow.get_market_flow_snapshot("it")

    assert [call["security_id_code"] for call in calls] == [21, 21]
    assert [call["type_flag"] for call in calls] == ["G", "L"]
    assert result["status"] == "success"
    assert result["sector"]["key"] == "it"
    assert result["movers"]["gainers"][0]["symbol"] == "INFY"
    assert result["movers"]["losers"][0]["symbol"] == "WIPRO"
    assert result["movers"]["gainers"][0]["sector"] == "Information Technology"
    assert result["sector_index"]["last_price"] == 25000
    assert result["capabilities"]["sector_index_quote"] is True


def test_chart_flow_sector_movers_marks_partial_provider_results(monkeypatch):
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(market_flow, "_sector_cache", {})
    calls = {"count": 0}

    def fake_fetch(**kwargs):
        calls["count"] += 1
        if kwargs["type_flag"] == "L":
            raise RuntimeError("sector losers unavailable")
        return {"status": True, "data": [{
            "exchange": "NSE", "symbol": "INFY", "ltp": 1500,
            "per_change": 2, "volume": 1000,
        }]}

    monkeypatch.setattr(market_flow, "fetch_movers", fake_fetch)
    monkeypatch.setattr(market_flow, "fetch_index", lambda _index: (_ for _ in ()).throw(RuntimeError("index quote unavailable")))

    result = market_flow.get_market_flow_snapshot("it")

    assert result["status"] == "partial"
    assert len(result["movers"]["gainers"]) == 1
    assert result["movers"]["losers"] == []
    assert result["errors"][0]["type"] == "losers"


def test_chart_flow_rejects_unknown_sector_key():
    with pytest.raises(HTTPException) as exc:
        market_flow.get_market_flow_snapshot("not-a-sector")

    assert exc.value.status_code == 404


def test_chart_flow_uses_one_shared_route_for_market_and_sector_queries():
    routes = [
        route for route in market_flow.router.routes
        if getattr(route, "path", None) == "/"
        and "GET" in getattr(route, "methods", set())
    ]

    assert len(routes) == 1
    assert "sector" in {parameter.name for parameter in routes[0].dependant.query_params}


def test_chart_flow_sector_cache_reuses_recent_provider_snapshot(monkeypatch):
    monkeypatch.setattr(market_flow, "_sector_cache", {})
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)
    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        return {"status": True, "data": [{
            "exchange": "NSE", "symbol": "INFY", "ltp": 1500,
            "per_change": 1, "volume": 100,
        }]}

    monkeypatch.setattr(market_flow, "fetch_movers", fake_fetch)
    monkeypatch.setattr(market_flow, "fetch_index", lambda index: {
        "name": index["name"], "exchange": index["exchange"], "symbol": index["symbol"],
        "last_price": 25000, "status": "success",
    })

    first = market_flow.get_market_flow_snapshot("it")
    second = market_flow.get_market_flow_snapshot("it")

    assert first == second
    assert len(calls) == 2


def test_chart_flow_can_load_all_sector_index_quotes_from_shared_snapshot(monkeypatch):
    monkeypatch.setattr(market_flow, "fetch_all_cash_movers", lambda: (
        {"gainers": [], "losers": []}, []
    ))
    monkeypatch.setattr(market_flow, "fetch_index", lambda index: {
        "name": index["name"],
        "exchange": index["exchange"],
        "symbol": index["symbol"],
        "last_price": 1000,
        "previous_close": 990,
        "change": 10,
        "percent_change": 1.01,
        "status": "success",
    })

    result = market_flow.get_market_flow_snapshot(include_sector_indices=True)

    assert len(result["sector_indices"]) == len(market_flow.SECTOR_UNIVERSES)
    assert result["capabilities"]["sector_index_quotes"] is True
    assert result["capabilities"]["sector_index_performance"] is True
    assert result["sector_indices"][0]["percent_change"] == 1.01
    assert result["sector_indices"][0]["key"] in {
        item["key"] for item in market_flow.SECTOR_UNIVERSES
    }
