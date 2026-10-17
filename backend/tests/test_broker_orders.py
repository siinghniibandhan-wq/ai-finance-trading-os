from types import SimpleNamespace
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.routes import broker_orders


def request_payload():
    return broker_orders.BrokerOrderRequest(
        side="BUY",
        symbol="RELIANCE-EQ",
        exchange="NSE",
        product_type="DELIVERY",
        order_type="MARKET",
        validity="DAY",
        quantity=1,
        quote_price=Decimal("1450.00"),
    )


def test_place_order_returns_acknowledgement_without_updating_portfolio(monkeypatch):
    captured = {}

    def fake_gateway(path, method, payload):
        captured.update(payload)
        return {"status": "success", "data": {"orderid": "ORD-123"}}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    result = broker_orders.place_broker_order(
        request_payload(), current_user=SimpleNamespace(id=7)
    )

    assert result["status"] == "submitted"
    assert result["order_id"] == "ORD-123"
    assert result["portfolio_updated"] is False
    assert "does not confirm execution" in result["message"]
    assert captured["client_id"].startswith("financial-os-7-")
    assert captured["tradingsymbol"] == "RELIANCE-EQ"
    assert captured["transaction_type"] == "BUY"
    assert captured["product"] == "CNC"
    assert captured["ref_price"] == "1450.00"
    assert result["client_reference"] == captured["client_id"]


def test_each_order_gets_a_unique_client_reference(monkeypatch):
    references = []

    def fake_gateway(path, method, payload):
        references.append(payload["client_id"])
        return {"success": True, "order_id": f"ORD-{len(references)}"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    user = SimpleNamespace(id=7)

    broker_orders.place_broker_order(request_payload(), current_user=user)
    broker_orders.place_broker_order(request_payload(), current_user=user)

    assert len(references) == 2
    assert references[0] != references[1]


@pytest.mark.parametrize(
    "gateway_result",
    [
        {"status": "rejected", "message": "Insufficient funds"},
        {"success": True, "data": {"status": "rejected", "message": "Rejected by broker"}},
        {"data": {"success": False, "error": "Invalid order"}},
    ],
)
def test_explicit_gateway_rejection_is_not_reported_as_accepted(monkeypatch, gateway_result):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: gateway_result
    )

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(), current_user=SimpleNamespace(id=7)
        )

    assert error.value.status_code == 502


def test_ambiguous_gateway_response_requires_order_book_check(monkeypatch):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: {"message": "received"}
    )

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(), current_user=SimpleNamespace(id=7)
        )

    assert error.value.status_code == 502
    assert "Check the broker order book" in error.value.detail
