from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import order_flow


def test_extract_bearer_token_from_websocket_subprotocol_without_query_string():
    assert order_flow.extract_bearer_token("financial-os, bearer.header.payload.signature") == "header.payload.signature"
    assert order_flow.extract_bearer_token("financial-os") is None
    assert order_flow.extract_bearer_token(None) is None


def test_order_flow_websocket_uses_existing_bearer_session_and_sends_live_snapshot(monkeypatch):
    app = FastAPI()
    app.include_router(order_flow.stream_router)
    client = TestClient(app)

    def fake_get_db():
        yield object()

    monkeypatch.setattr(order_flow, "get_db", fake_get_db)
    monkeypatch.setattr(
        order_flow,
        "get_current_user",
        lambda authorization, credentials, db: object()
        if authorization == "Bearer valid-financial-os-token"
        else (_ for _ in ()).throw(ValueError("invalid token")),
    )
    calls = []

    def fake_snapshot(symbol, *, ensure_started):
        calls.append((symbol, ensure_started))
        return {
            "status": "success",
            "feed": {"status": "fresh", "last_tick_at": "2026-11-18T09:30:00+00:00"},
            "futures_contracts": [{"symbol": "NIFTY", "price": 25000.5, "oi": 1000, "volume": 500}],
            "option_contracts": [],
            "option_oi_by_strike": [],
        }

    monkeypatch.setattr(order_flow, "get_order_flow_snapshot", fake_snapshot)

    with client.websocket_connect(
        "/api/order-flow/stream?symbol=NIFTY",
        subprotocols=["financial-os", "bearer.valid-financial-os-token"],
    ) as websocket:
        payload = websocket.receive_json()

    assert payload["status"] == "success"
    assert payload["futures_contracts"][0]["price"] == 25000.5
    assert calls[0] == ("NIFTY", True)
