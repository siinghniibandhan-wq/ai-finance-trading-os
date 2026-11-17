"""Regression tests for the authenticated Order Flow snapshot route."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.order_flow import router


def test_snapshot_route_requires_existing_financial_os_bearer_session():
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).get("/api/order-flow/snapshot")
    assert response.status_code == 401
    assert "token" in response.json()["detail"].lower()


def test_snapshot_route_uses_existing_auth_dependency_and_preserves_contract(monkeypatch):
    from app.routes import order_flow

    app = FastAPI()
    app.include_router(router)

    def fake_snapshot(symbol=None):
        return {
            "status": "success",
            "source": "m.Stock via Financial OS derivatives gateway",
            "read_only": True,
            "as_of": "2026-11-17T09:20:00+00:00",
            "feed": {"status": "fresh", "last_tick_at": "2026-11-17T09:20:00+00:00", "age_seconds": 1},
            "futures_contracts": [],
            "contract_months": [],
            "option_oi_by_strike": [],
            "historical_oi_included": False,
            "coverage": {"state": "ready"},
            "stream": {"running": True},
        }

    monkeypatch.setattr(order_flow, "get_order_flow_snapshot", fake_snapshot)
    from app.routes.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1}
    response = TestClient(app).get("/api/order-flow/snapshot?symbol=nifty")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["coverage"] == {"state": "ready"}
    assert body["stream"] == {"running": True}
    assert body["historical_oi_included"] is False
