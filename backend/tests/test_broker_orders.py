from types import SimpleNamespace
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base
from app import models
from fastapi import HTTPException

from app.routes import broker_orders


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'broker-orders-test.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def request_payload(client_id=None):
    return broker_orders.BrokerOrderRequest(
        side="BUY",
        symbol="RELIANCE-EQ",
        exchange="NSE",
        product_type="DELIVERY",
        order_type="MARKET",
        validity="DAY",
        quantity=1,
        quote_price=Decimal("1450.00"),
        client_id=client_id,
    )


def test_place_order_returns_acknowledgement_without_updating_portfolio(monkeypatch, db_session):
    captured = {}

    def fake_gateway(path, method, payload):
        captured.update(payload)
        return {"status": "success", "data": {"orderid": "ORD-123"}}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    result = broker_orders.place_broker_order(
        request_payload(), db=db_session, current_user=SimpleNamespace(id=7)
    )

    assert result["status"] == "submitted"
    assert result["order_id"] == "ORD-123"
    assert result["portfolio_updated"] is False
    assert "does not confirm execution" in result["message"]
    assert captured["client_id"].startswith("financial-os-7-")


def test_each_order_gets_a_unique_client_id_when_not_supplied(monkeypatch, db_session):
    client_ids = []

    def fake_gateway(path, method, payload):
        client_ids.append(payload["client_id"])
        return {"success": True, "order_id": f"ORD-{len(client_ids)}"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    user = SimpleNamespace(id=7)

    broker_orders.place_broker_order(request_payload(), current_user=user)
    broker_orders.place_broker_order(request_payload(), current_user=user)

    assert len(client_ids) == 2
    assert client_ids[0] != client_ids[1]


def test_supplied_client_id_is_forwarded_unchanged(monkeypatch, db_session):
    captured = {}

    def fake_gateway(path, method, payload):
        captured.update(payload)
        return {"success": True, "order_id": "ORD-CLIENT-ID"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    result = broker_orders.place_broker_order(
        request_payload("finos-retry-123"), db=db_session, current_user=SimpleNamespace(id=7)
    )

    assert result["order_id"] == "ORD-CLIENT-ID"
    assert captured["client_id"] == "finos-retry-123"
    assert "client_reference" not in captured


def test_order_uses_gateway_order_endpoint(monkeypatch, db_session):
    captured = {}

    def fake_gateway(path, method, payload):
        captured["path"] = path
        captured["method"] = method
        return {"success": True, "order_id": "ORD-PATH"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    broker_orders.place_broker_order(request_payload(), current_user=SimpleNamespace(id=7))

    assert captured == {"path": broker_orders.GATEWAY_ORDER_PLACE_PATH, "method": "POST"}
    assert broker_orders.GATEWAY_ORDER_PLACE_PATH == "/order"


@pytest.mark.parametrize(
    "gateway_result",
    [
        {"status": "rejected", "message": "Insufficient funds"},
        {"success": True, "data": {"status": "rejected", "message": "Rejected by broker"}},
        {"data": {"success": False, "error": "Invalid order"}},
    ],
)
def test_explicit_gateway_rejection_is_not_reported_as_accepted(monkeypatch, gateway_result, db_session):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: gateway_result
    )

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(), current_user=SimpleNamespace(id=7)
        )

    assert error.value.status_code == 502


def test_ambiguous_gateway_response_requires_order_book_check(monkeypatch, db_session):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: {"message": "received"}
    )

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(), current_user=SimpleNamespace(id=7)
        )

    assert error.value.status_code == 502
    assert "Check the broker order book" in error.value.detail

def test_gateway_requests_fail_closed_without_shared_secret(monkeypatch):
    monkeypatch.setattr(broker_orders, "GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(broker_orders, "GATEWAY_SECRET", "")

    with pytest.raises(HTTPException) as error:
        broker_orders._gateway_request("/order", "POST", {"client_id": "retry-1"})

    assert error.value.status_code == 503
    assert "MSTOCK_GATEWAY_SECRET" in error.value.detail



def test_gateway_rejects_public_http_endpoint_and_does_not_send_secret(monkeypatch):
    monkeypatch.setattr(broker_orders, "GATEWAY_URL", "http://54.153.201.74:8000")
    monkeypatch.setattr(broker_orders, "GATEWAY_SECRET", "test-secret")

    with pytest.raises(HTTPException) as error:
        broker_orders._gateway_request("/order", "POST", {"client_id": "retry-2"})

    assert error.value.status_code == 503
    assert "loopback HTTP" in error.value.detail


def test_real_order_and_order_book_routes_require_admin():
    from app.routes.auth import get_current_admin

    route_dependencies = {
        route.endpoint.__name__: {
            dependency.call
            for dependency in route.dependant.dependencies
        }
        for route in broker_orders.router.routes
    }

    assert get_current_admin in route_dependencies["place_broker_order"]
    assert get_current_admin in route_dependencies["list_broker_orders"]


def test_duplicate_client_id_is_blocked_from_persistent_database_record(monkeypatch, db_session):
    calls = []

    def fake_gateway(path, method, payload):
        calls.append(payload["client_id"])
        return {"success": True, "order_id": "ORD-PERSISTENT"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    user = SimpleNamespace(id=77)
    broker_orders.place_broker_order(request_payload("persistent-key-1"), db=db_session, current_user=user)

    # Simulate a backend process restart by using a fresh ORM session against
    # the same persistent database file.
    engine = db_session.get_bind()
    from sqlalchemy.orm import Session
    restarted_session = Session(bind=engine, expire_on_commit=False)
    try:
        with pytest.raises(HTTPException) as error:
            broker_orders.place_broker_order(
                request_payload("persistent-key-1"), db=restarted_session, current_user=user
            )
        assert error.value.status_code == 409
    finally:
        restarted_session.close()

    assert calls == ["persistent-key-1"]


def test_same_client_id_with_different_payload_is_blocked(monkeypatch, db_session):
    calls = []
    monkeypatch.setattr(
        broker_orders,
        "_gateway_request",
        lambda path, method, payload: calls.append(payload) or {"success": True, "order_id": "ORD-1"},
    )
    user = SimpleNamespace(id=78)
    broker_orders.place_broker_order(request_payload("payload-key-1"), db=db_session, current_user=user)
    changed = request_payload("payload-key-1")
    changed.quantity = 2

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(changed, db=db_session, current_user=user)

    assert error.value.status_code == 409
    assert len(calls) == 1
