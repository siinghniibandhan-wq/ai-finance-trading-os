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



def test_postgres_reconciles_mocked_partial_fills_once(monkeypatch):
    """Exercise the real reconciliation SQL against disposable PostgreSQL only."""
    from sqlalchemy import text
    from app.routes import broker_reconciliation

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    user_email = f"{uuid4().hex}@example.invalid"
    client_id = f"pg-reconcile-{uuid4().hex}"
    trade_rows = [
        {
            "TRADE_NUMBER": "MOCK-TRADE-1",
            "EXCH_ORDER_NUMBER": "MOCK-EXCHANGE-ORDER-1",
            "broker_order_id": "MOCK-BROKER-ORDER-1",
            "client_reference": client_id,
            "SYMBOL": "RELIANCE-EQ",
            "BUY_SELL": "BUY",
            "QUANTITY": "2",
            "PRICE": "100.00",
            "ORDER_DATE_TIME": "2026-10-17 10:00:00",
            "EXCHANGE": "NSE",
        },
        {
            "TRADE_NUMBER": "MOCK-TRADE-2",
            "EXCH_ORDER_NUMBER": "MOCK-EXCHANGE-ORDER-1",
            "broker_order_id": "MOCK-BROKER-ORDER-1",
            "client_reference": client_id,
            "SYMBOL": "RELIANCE-EQ",
            "BUY_SELL": "BUY",
            "QUANTITY": "3",
            "PRICE": "101.00",
            "ORDER_DATE_TIME": "2026-10-17 10:01:00",
            "EXCHANGE": "NSE",
        },
    ]

    try:
        with SessionFactory() as setup:
            # These legacy ledger tables are SQL-managed rather than Base metadata.
            setup.execute(text("""
                CREATE TABLE IF NOT EXISTS investments (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL, investment_type VARCHAR(50) NOT NULL,
                    symbol VARCHAR(100), quantity NUMERIC(18,6) NOT NULL,
                    buy_price NUMERIC(18,4) NOT NULL, current_price NUMERIC(18,4),
                    buy_date DATE NOT NULL, broker VARCHAR(255), fees NUMERIC(18,2) DEFAULT 0,
                    notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            setup.execute(text("""
                CREATE TABLE IF NOT EXISTS investment_transactions (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                    investment_id INTEGER NOT NULL, transaction_type VARCHAR(10) NOT NULL,
                    quantity NUMERIC(18,6) NOT NULL, price NUMERIC(18,4) NOT NULL,
                    fees NUMERIC(18,2) DEFAULT 0, transaction_date DATE NOT NULL,
                    notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(12) NOT NULL DEFAULT 'ACTIVE',
                    void_reason TEXT, voided_at TIMESTAMP,
                    CHECK (transaction_type IN ('BUY', 'SELL')),
                    CHECK (quantity > 0), CHECK (price > 0), CHECK (fees >= 0)
                )
            """))
            setup.execute(text("""
                CREATE TABLE IF NOT EXISTS broker_reconciled_fills (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                    broker_trade_id VARCHAR(255) NOT NULL,
                    exchange_order_id VARCHAR(255) NOT NULL,
                    client_reference VARCHAR(120) NOT NULL,
                    investment_transaction_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, broker_trade_id, exchange_order_id)
                )
            """))
            user = models.User(name="Reconciliation integration test", email=user_email)
            setup.add(user)
            setup.commit()
            user_id = user.id
            investment_id = setup.execute(text("""
                INSERT INTO investments
                    (user_id, name, investment_type, symbol, quantity, buy_price, buy_date, broker)
                VALUES (:uid, 'Reliance test', 'STOCK', 'RELIANCE-EQ', 0, 100, '2026-10-17', 'm.Stock')
                RETURNING id
            """), {"uid": user_id}).scalar_one()
            setup.add(models.BrokerOrderSubmission(
                user_id=user_id, investment_id=investment_id, symbol="RELIANCE-EQ",
                exchange="NSE", side="BUY", quantity=5, client_id=client_id,
                payload_hash="a" * 64, status="ACKNOWLEDGED",
                gateway_order_id="MOCK-BROKER-ORDER-1",
            ))
            setup.commit()

        monkeypatch.setenv("MSTOCK_ORDER_ID_MAPPING_VERIFIED", "1")
        monkeypatch.setattr(
            broker_reconciliation, "_gateway_request",
            lambda path, method: {"success": True, "data": trade_rows},
        )

        with SessionFactory() as session:
            result = broker_reconciliation.reconcile_broker_fills(
                db=session, current_user=SimpleNamespace(id=user_id)
            )
            assert result["imported_count"] == 2
            assert result["duplicate_count"] == 0

        with SessionFactory() as verify:
            quantity = verify.execute(text(
                "SELECT quantity FROM investments WHERE id=:id AND user_id=:uid"
            ), {"id": investment_id, "uid": user_id}).scalar_one()
            ledger_rows = verify.execute(text("""
                SELECT transaction_type, quantity FROM investment_transactions
                WHERE user_id=:uid AND investment_id=:iid ORDER BY id
            """), {"uid": user_id, "iid": investment_id}).fetchall()
            assert Decimal(str(quantity)) == Decimal("5.000000")
            assert [(r.transaction_type, Decimal(str(r.quantity))) for r in ledger_rows] == [
                ("BUY", Decimal("2.000000")), ("BUY", Decimal("3.000000"))
            ]

        # Replaying the same broker trade-book must not double the holding or ledger.
        with SessionFactory() as session:
            replay = broker_reconciliation.reconcile_broker_fills(
                db=session, current_user=SimpleNamespace(id=user_id)
            )
            assert replay["imported_count"] == 0
            assert replay["duplicate_count"] == 2

        with SessionFactory() as verify:
            quantity = verify.execute(text(
                "SELECT quantity FROM investments WHERE id=:id AND user_id=:uid"
            ), {"id": investment_id, "uid": user_id}).scalar_one()
            ledger_count = verify.execute(text("""
                SELECT COUNT(*) FROM investment_transactions
                WHERE user_id=:uid AND investment_id=:iid
            """), {"uid": user_id, "iid": investment_id}).scalar_one()
            assert Decimal(str(quantity)) == Decimal("5.000000")
            assert ledger_count == 2

        # A mocked SELL exceeding the available ledger must be skipped safely.
        sell_client_id = f"pg-reconcile-sell-{uuid4().hex}"
        with SessionFactory() as setup:
            setup.add(models.BrokerOrderSubmission(
                user_id=user_id, investment_id=investment_id, symbol="RELIANCE-EQ",
                exchange="NSE", side="SELL", quantity=6, client_id=sell_client_id,
                payload_hash="b" * 64, status="ACKNOWLEDGED",
                gateway_order_id="MOCK-BROKER-SELL-1",
            ))
            setup.commit()
        sell_row = {
            "TRADE_NUMBER": "MOCK-SELL-TRADE-1",
            "EXCH_ORDER_NUMBER": "MOCK-SELL-EXCHANGE-ORDER-1",
            "broker_order_id": "MOCK-BROKER-SELL-1",
            "client_reference": sell_client_id,
            "SYMBOL": "RELIANCE-EQ",
            "BUY_SELL": "SELL",
            "QUANTITY": "6",
            "PRICE": "102.00",
            "ORDER_DATE_TIME": "2026-10-17 10:02:00",
            "EXCHANGE": "NSE",
        }
        monkeypatch.setattr(
            broker_reconciliation, "_gateway_request",
            lambda path, method: {"success": True, "data": [sell_row]},
        )
        with SessionFactory() as session:
            sell_result = broker_reconciliation.reconcile_broker_fills(
                db=session, current_user=SimpleNamespace(id=user_id)
            )
            assert sell_result["imported_count"] == 0
            assert sell_result["skipped_count"] == 1
        with SessionFactory() as verify:
            quantity = verify.execute(text(
                "SELECT quantity FROM investments WHERE id=:id AND user_id=:uid"
            ), {"id": investment_id, "uid": user_id}).scalar_one()
            ledger_count = verify.execute(text("""
                SELECT COUNT(*) FROM investment_transactions
                WHERE user_id=:uid AND investment_id=:iid
            """), {"uid": user_id, "iid": investment_id}).scalar_one()
            marker_count = verify.execute(text("""
                SELECT COUNT(*) FROM broker_reconciled_fills
                WHERE user_id=:uid AND broker_trade_id='MOCK-SELL-TRADE-1'
            """), {"uid": user_id}).scalar_one()
            assert Decimal(str(quantity)) == Decimal("5.000000")
            assert ledger_count == 2
            assert marker_count == 0

        # Force a ledger insert failure in PostgreSQL and prove the savepoint
        # and outer transaction leave neither a fill marker nor a quantity change.
        rollback_client_id = f"pg-reconcile-rollback-{uuid4().hex}"
        with SessionFactory() as setup:
            setup.add(models.BrokerOrderSubmission(
                user_id=user_id, investment_id=investment_id, symbol="RELIANCE-EQ",
                exchange="NSE", side="BUY", quantity=1, client_id=rollback_client_id,
                payload_hash="c" * 64, status="ACKNOWLEDGED",
                gateway_order_id="MOCK-BROKER-ROLLBACK-1",
            ))
            setup.connection().exec_driver_sql("""
                CREATE OR REPLACE FUNCTION fail_mock_reconciliation_insert()
                RETURNS trigger LANGUAGE plpgsql AS $func$
                BEGIN
                    IF NEW.notes LIKE '%%MOCK-ROLLBACK-TRADE%%' THEN
                        RAISE EXCEPTION 'simulated ledger write failure';
                    END IF;
                    RETURN NEW;
                END;
                $func$
            """)
            setup.execute(text("""
                DROP TRIGGER IF EXISTS fail_mock_reconciliation_insert_trigger
                ON investment_transactions
            """))
            setup.execute(text("""
                CREATE TRIGGER fail_mock_reconciliation_insert_trigger
                BEFORE INSERT ON investment_transactions
                FOR EACH ROW EXECUTE FUNCTION fail_mock_reconciliation_insert()
            """))
            setup.commit()
        rollback_row = {
            "TRADE_NUMBER": "MOCK-ROLLBACK-TRADE",
            "EXCH_ORDER_NUMBER": "MOCK-ROLLBACK-EXCHANGE-ORDER",
            "broker_order_id": "MOCK-BROKER-ROLLBACK-1",
            "client_reference": rollback_client_id,
            "SYMBOL": "RELIANCE-EQ",
            "BUY_SELL": "BUY",
            "QUANTITY": "1",
            "PRICE": "103.00",
            "ORDER_DATE_TIME": "2026-10-17 10:03:00",
            "EXCHANGE": "NSE",
        }
        monkeypatch.setattr(
            broker_reconciliation, "_gateway_request",
            lambda path, method: {"success": True, "data": [rollback_row]},
        )
        with SessionFactory() as session:
            with pytest.raises(HTTPException) as failed_import:
                broker_reconciliation.reconcile_broker_fills(
                    db=session, current_user=SimpleNamespace(id=user_id)
                )
            assert failed_import.value.status_code == 500
        with SessionFactory() as verify:
            quantity = verify.execute(text(
                "SELECT quantity FROM investments WHERE id=:id AND user_id=:uid"
            ), {"id": investment_id, "uid": user_id}).scalar_one()
            ledger_count = verify.execute(text("""
                SELECT COUNT(*) FROM investment_transactions
                WHERE user_id=:uid AND investment_id=:iid
            """), {"uid": user_id, "iid": investment_id}).scalar_one()
            marker_count = verify.execute(text("""
                SELECT COUNT(*) FROM broker_reconciled_fills
                WHERE user_id=:uid AND broker_trade_id='MOCK-ROLLBACK-TRADE'
            """), {"uid": user_id}).scalar_one()
            assert Decimal(str(quantity)) == Decimal("5.000000")
            assert ledger_count == 2
            assert marker_count == 0
            verify.execute(text("""
                DROP TRIGGER IF EXISTS fail_mock_reconciliation_insert_trigger
                ON investment_transactions
            """))
            verify.execute(text("DROP FUNCTION IF EXISTS fail_mock_reconciliation_insert()"))
            verify.commit()
    finally:
        # Disposable CI PostgreSQL only. Keep legacy tables out of Base metadata.
        Base.metadata.drop_all(engine)
        engine.dispose()
