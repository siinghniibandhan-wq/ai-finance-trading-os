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
    assert result["scope"]["universe"] == "Provider-ranked cash-market gainers and losers requested with SecurityIdCode=0 (ALL)"
    assert result["scope"]["completeness"] == "provider_ranked_sample"
    assert result["market_summary"]["sample_only"] is True
    assert result["market_summary"]["breadth_complete"] is False


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
        "last_price": 25000, "previous_close": 24900,
        "change": 100, "percent_change": (100 / 24900) * 100,
        "status": "success",
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
    assert result["capabilities"]["sector_index_performance"] is True
    assert all("index-quote contract supplies a current index price only" not in item for item in result["limitations"])


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
    import inspect

    parameters = inspect.signature(market_flow.get_market_flow_snapshot).parameters
    assert "sector" in parameters
    assert "include_sector_indices" in parameters
    assert len([
        route for route in market_flow.router.routes
        if getattr(route, "endpoint", None) is market_flow.get_market_flow_snapshot
    ]) == 1


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
        {"gainers": [], "losers": []}, [], {}
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


def test_chart_flow_caches_complete_sector_index_scan(monkeypatch):
    monkeypatch.setattr(market_flow, "_sector_index_cache", {
        "loaded_at": 0.0, "results": [], "errors": [],
    })
    calls = {"count": 0}

    def fake_fetch(index):
        calls["count"] += 1
        return {
            "name": index["name"], "exchange": index["exchange"], "symbol": index["symbol"],
            "last_price": 1000, "previous_close": 990, "change": 10,
            "percent_change": 1.01, "status": "success",
        }

    monkeypatch.setattr(market_flow, "fetch_index", fake_fetch)
    first, first_errors = market_flow.fetch_sector_index_snapshots()
    second, second_errors = market_flow.fetch_sector_index_snapshots()

    assert len(first) == len(market_flow.SECTOR_UNIVERSES)
    assert first == second
    assert first_errors == second_errors == []
    assert calls["count"] == len(market_flow.SECTOR_UNIVERSES)


def test_chart_flow_sector_universe_matches_mstock_documented_security_id_codes():
    expected = {
        "auto": 9,
        "private-bank": 10,
        "fmcg": 20,
        "it": 21,
        "media": 22,
        "metal": 23,
        "pharma": 24,
        "psu-bank": 25,
        "realty": 26,
        "energy": 33,
        "infrastructure": 34,
        "mnc": 35,
        "services": 37,
        "consumer-durables": 59,
        "financial-services": 60,
        "oil-gas": 61,
        "healthcare": 62,
    }

    actual = {item["key"]: item["security_id_code"] for item in market_flow.SECTOR_UNIVERSES}

    assert actual == expected
    assert len({item["index_symbol"] for item in market_flow.SECTOR_UNIVERSES}) == len(expected)


def test_mover_rejection_reason_drops_impossible_and_inconsistent_rows():
    from app.routes.market_movers import mover_rejection_reason as check

    good = {"ltp": 732.2, "change": 42.7, "percent_change": 6.19, "volume": 6227379}
    assert check(good, require_volume=True) is None
    # BSE debt-like rows seen in production: huge moves, impossible drops, zero volume
    assert check({"ltp": 99786, "percent_change": -232, "volume": 0}) == "impossible_percent_change"
    assert check({"ltp": 15360, "change": -10, "percent_change": -200.0, "volume": 0}) == "impossible_percent_change"
    assert check({"ltp": 100, "change": 2, "percent_change": 995, "volume": 5}) == "percent_change_mismatch"
    assert check({"ltp": 99786, "percent_change": 995, "volume": 0}, require_volume=True) == "price_move_without_volume"
    assert check({"ltp": 0, "percent_change": 1}) == "invalid_price"
    assert check({"ltp": 10, "percent_change": None}) == "missing_percent_change"
    # sector lists may legitimately omit volume
    assert check({"ltp": 429.6, "percent_change": -2.0, "volume": 0}) is None


def test_chart_flow_all_universe_filters_bad_rows_and_reports_counts(monkeypatch):
    monkeypatch.setattr(market_flow.time, "sleep", lambda _seconds: None)

    def fake_fetch(**kwargs):
        return {"status": True, "data": [
            {"exchange": "BSE", "symbol": "11MGFL27", "ltp": 99786, "per_change": 995, "volume": 0},
            {"exchange": "BSE", "symbol": "DRA", "ltp": 16.35, "per_change": -139, "volume": 0},
            {"exchange": "NSE", "symbol": "INFY", "ltp": 1500, "per_change": 2.0, "change": 29.41, "volume": 1000},
        ]}

    monkeypatch.setattr(market_flow, "fetch_movers", fake_fetch)
    movers, errors, rejected = market_flow.fetch_all_cash_movers()

    assert errors == []
    symbols = {row["symbol"] for row in movers["gainers"] + movers["losers"]}
    assert symbols == {"INFY"}
    assert rejected["price_move_without_volume"] >= 1
    assert rejected["impossible_percent_change"] >= 1
