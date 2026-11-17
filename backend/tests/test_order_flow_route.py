from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import auth, order_flow


def test_order_flow_snapshot_requires_existing_bearer_auth(monkeypatch):
    app = FastAPI()
    app.include_router(order_flow.router)
    client = TestClient(app)

    response = client.get("/api/order-flow/snapshot")

    assert response.status_code == 401


def test_order_flow_snapshot_uses_existing_current_user_dependency(monkeypatch):
    app = FastAPI()
    app.include_router(order_flow.router)
    app.dependency_overrides[auth.get_current_user] = lambda: {"id": 123}
    monkeypatch.setattr(
        order_flow,
        "get_order_flow_snapshot",
        lambda symbol=None: {"status": "success", "symbol": symbol},
    )
    client = TestClient(app)

    response = client.get("/api/order-flow/snapshot?symbol=nifty")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "symbol": "NIFTY"}
