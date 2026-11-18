import pytest
from fastapi import HTTPException

from app.routes import market_movers, market_overview


def test_market_movers_rejects_gateway_error_status(monkeypatch):
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
        market_movers.get_market_movers(type="gainers", exchange=1, security_id_code=13, segment=1, limit=20)

    assert exc.value.status_code == 502
    assert "authentication required" in str(exc.value.detail).lower()


def test_market_movers_rejects_non_list_gateway_data(monkeypatch):
    monkeypatch.setattr(
        market_movers,
        "fetch_movers",
        lambda **_kwargs: {"status": "success", "data": {"unexpected": "shape"}},
    )

    with pytest.raises(HTTPException) as exc:
        market_movers.get_market_movers()

    assert exc.value.status_code == 502
    assert "invalid data" in str(exc.value.detail).lower()


def test_market_overview_rejects_gateway_error_status(monkeypatch):
    monkeypatch.setattr(
        market_overview,
        "fetch_movers",
        lambda **_kwargs: {
            "status": "error",
            "message": "m.Stock authentication required",
            "data": [],
        },
    )

    with pytest.raises(ValueError, match="authentication required"):
        market_overview.fetch_overview_movers("gainers")


def test_market_overview_rejects_non_list_gateway_data(monkeypatch):
    monkeypatch.setattr(
        market_overview,
        "fetch_movers",
        lambda **_kwargs: {"status": "success", "data": {"unexpected": "shape"}},
    )

    with pytest.raises(ValueError, match="invalid data"):
        market_overview.fetch_overview_movers("gainers")
