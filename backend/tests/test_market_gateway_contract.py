import pytest
from fastapi import HTTPException

from app.routes import market_movers, market_overview


TYPE_A_ROWS = [
    {
        "exchange": "NSE",
        "segment": "E",
        "security_id": 5258,
        "ltp": 732.2,
        "volume": 6227379,
        "per_change": 6.19,
        "change": 42.7,
        "symbol_name": "INDUSIND BANK LIMITED",
        "display_name": "INDUSIND BANK LIMITED",
        "symbol": "INDUSINDBK",
    }
]


def test_market_movers_accepts_type_a_boolean_success_and_normalizes_rows(monkeypatch):
    monkeypatch.setattr(
        market_movers,
        "fetch_movers",
        lambda **_kwargs: {
            "status": True,
            "message": "SUCCESS",
            "errorcode": "",
            "data": TYPE_A_ROWS,
        },
    )

    result = market_movers.get_market_movers(
        type="gainers", exchange=1, security_id_code=13, segment=1, limit=20
    )

    assert result["status"] == "success"
    assert result["type"] == "gainers"
    assert result["count"] == 1
    assert result["movers"][0] == {
        "symbol": "INDUSINDBK",
        "name": "INDUSIND BANK LIMITED",
        "exchange": "NSE",
        "segment": "E",
        "security_id": 5258,
        "ltp": 732.2,
        "change": 42.7,
        "percent_change": 6.19,
        "volume": 6227379,
        "instrument": None,
        "series": None,
        "isin": None,
    }


def test_market_movers_sends_loser_flag_to_gateway(monkeypatch):
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return {"status": True, "message": "SUCCESS", "data": TYPE_A_ROWS}

    monkeypatch.setattr(market_movers, "fetch_movers", fake_fetch)

    result = market_movers.get_market_movers(
        type="losers", exchange=1, security_id_code=13, segment=1, limit=20
    )

    assert captured["type_flag"] == "L"
    assert result["type"] == "losers"
    assert result["count"] == 1


def test_market_movers_rejects_type_a_boolean_error_status(monkeypatch):
    monkeypatch.setattr(
        market_movers,
        "fetch_movers",
        lambda **_kwargs: {
            "status": False,
            "message": "Invalid request. Please try again.",
            "errorcode": "IA401",
            "data": None,
        },
    )

    with pytest.raises(HTTPException) as exc:
        market_movers.get_market_movers(
            type="gainers", exchange=1, security_id_code=13, segment=1, limit=20
        )

    assert exc.value.status_code == 502
    assert "invalid request" in str(exc.value.detail).lower()


def test_market_movers_rejects_legacy_gateway_error_status(monkeypatch):
    monkeypatch.setattr(
        market_movers,
        "fetch_movers",
        lambda **_kwargs: {
            "status": "error",
            "message": "m.Stock authentication required",
            "data": [],
        },
    )

    with pytest.raises(HTTPException) as exc:
        market_movers.get_market_movers(
            type="gainers", exchange=1, security_id_code=13, segment=1, limit=20
        )

    assert exc.value.status_code == 502
    assert "authentication required" in str(exc.value.detail).lower()


def test_market_movers_rejects_non_list_gateway_data(monkeypatch):
    monkeypatch.setattr(
        market_movers,
        "fetch_movers",
        lambda **_kwargs: {"status": True, "data": {"unexpected": "shape"}},
    )

    with pytest.raises(HTTPException) as exc:
        market_movers.get_market_movers(
            type="gainers", exchange=1, security_id_code=13, segment=1, limit=20
        )

    assert exc.value.status_code == 502
    assert "invalid data" in str(exc.value.detail).lower()


def test_market_overview_accepts_type_a_boolean_success(monkeypatch):
    monkeypatch.setattr(
        market_overview,
        "fetch_movers",
        lambda **_kwargs: {
            "status": True,
            "message": "SUCCESS",
            "data": TYPE_A_ROWS,
        },
    )

    result = market_overview.fetch_overview_movers("losers")

    assert len(result) == 1
    assert result[0]["symbol"] == "INDUSINDBK"
    assert result[0]["percent_change"] == 6.19


def test_market_overview_rejects_type_a_boolean_error_status(monkeypatch):
    monkeypatch.setattr(
        market_overview,
        "fetch_movers",
        lambda **_kwargs: {
            "status": False,
            "message": "m.Stock authentication required",
            "data": None,
        },
    )

    with pytest.raises(ValueError, match="authentication required"):
        market_overview.fetch_overview_movers("gainers")


def test_market_overview_rejects_non_list_gateway_data(monkeypatch):
    monkeypatch.setattr(
        market_overview,
        "fetch_movers",
        lambda **_kwargs: {"status": True, "data": {"unexpected": "shape"}},
    )

    with pytest.raises(ValueError, match="invalid data"):
        market_overview.fetch_overview_movers("gainers")
