"""Order Flow snapshot must remain behind the existing bearer-session auth."""
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from app.routes.auth import get_current_user
from app.routes.order_flow import router
from app.routes import order_flow as order_flow_route


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_order_flow_snapshot_rejects_anonymous_requests():
    response = client.get("/api/order-flow/snapshot?symbol=NIFTY")

    assert response.status_code == 401



def test_order_flow_accepts_ampersand_symbols_used_by_derivatives_universe(monkeypatch):
    monkeypatch.setattr(
        order_flow_route,
        "get_order_flow_snapshot",
        lambda symbol: {"status": "success", "symbol": symbol},
    )

    result = order_flow_route.order_flow_snapshot("GVT&D", _current_user=object())

    assert result == {"status": "success", "symbol": "GVT&D"}


def test_order_flow_rejects_invalid_or_empty_symbols():
    for symbol in ("NIFTY/../admin", "&&"):
        with pytest.raises(HTTPException) as error:
            order_flow_route.order_flow_snapshot(symbol, _current_user=object())
        assert error.value.status_code == 400
