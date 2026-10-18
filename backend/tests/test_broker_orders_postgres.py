"""PostgreSQL integration test for durable broker-order idempotency.

Runs only when BROKER_TEST_DATABASE_URL points at an isolated test database.
No live broker calls are made; the gateway is mocked.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.database.database import Base
from app.routes import broker_orders


DATABASE_URL = os.getenv("BROKER_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="BROKER_TEST_DATABASE_URL is not configured",
)


def test_postgres_blocks_simultaneous_duplicate_order(monkeypatch):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    client_id = f"pg-concurrent-{uuid4().hex}"
    entered_gateway = Event()
    release_gateway = Event()
    gateway_calls = []

    try:
        with SessionFactory() as setup:
            user = models.User(name="Broker order test", email=f"{uuid4().hex}@example.invalid")
            setup.add(user)
            setup.commit()
            user_id = user.id
            setup.add(models.BrokerTradingControl(id=1, enabled=True, updated_by=user_id))
            setup.commit()

        def fake_gateway(path, method, payload):
            gateway_calls.append(payload["client_id"])
            entered_gateway.set()
            assert release_gateway.wait(timeout=10)
            return {"success": True, "order_id": "MOCK-POSTGRES-ORDER"}

        monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)

        def submit():
            with SessionFactory() as session:
                request = broker_orders.BrokerOrderRequest(
                    side="BUY",
                    symbol="RELIANCE-EQ",
                    exchange="NSE",
                    product_type="DELIVERY",
                    order_type="MARKET",
                    validity="DAY",
                    quantity=1,
                    price=Decimal("0"),
                    quote_price=Decimal("1450.00"),
                    client_id=client_id,
                )
                return broker_orders.place_broker_order(
                    request,
                    db=session,
                    current_user=SimpleNamespace(id=user_id),
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(submit)
            assert entered_gateway.wait(timeout=10), "First request never reached mocked gateway"
            second = pool.submit(submit)
            try:
                with pytest.raises(HTTPException) as duplicate:
                    second.result(timeout=10)
                assert duplicate.value.status_code == 409
            finally:
                release_gateway.set()
            assert first.result(timeout=10)["order_id"] == "MOCK-POSTGRES-ORDER"

        assert gateway_calls == [client_id]

        # A fresh session (the same persistence boundary as a process restart)
        # must still see the reservation and refuse another gateway call.
        with SessionFactory() as restarted_session:
            request = broker_orders.BrokerOrderRequest(
                side="BUY",
                symbol="RELIANCE-EQ",
                exchange="NSE",
                product_type="DELIVERY",
                order_type="MARKET",
                validity="DAY",
                quantity=1,
                price=Decimal("0"),
                quote_price=Decimal("1450.00"),
                client_id=client_id,
            )
            with pytest.raises(HTTPException) as duplicate_after_restart:
                broker_orders.place_broker_order(
                    request,
                    db=restarted_session,
                    current_user=SimpleNamespace(id=user_id),
                )
            assert duplicate_after_restart.value.status_code == 409
        assert gateway_calls == [client_id]
    finally:
        release_gateway.set()
        # This workflow uses a disposable PostgreSQL service/database.
        Base.metadata.drop_all(engine)
        engine.dispose()
