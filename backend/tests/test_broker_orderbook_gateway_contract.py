from types import SimpleNamespace

from app.routes import broker_orders


def test_order_book_uses_the_gateway_route_that_exists(monkeypatch):
    calls = []

    def fake_gateway(path, method, payload=None, query=None):
        calls.append((path, method, query))
        return {"status": "success", "count": 0, "data": [], "normalized": []}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)

    result = broker_orders.list_broker_orders(
        current_user=SimpleNamespace(id=7),
        status="COMPLETE",
    )

    assert broker_orders.GATEWAY_ORDER_BOOK_PATH == "/orderbook"
    assert calls == [("/orderbook", "GET", {"status": "COMPLETE"})]
    assert result["broker_response"]["status"] == "success"
