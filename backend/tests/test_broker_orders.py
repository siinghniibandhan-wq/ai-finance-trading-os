from types import SimpleNamespace
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
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
    # Existing order tests explicitly exercise the enabled state. Dedicated
    # tests below remove this row to verify the fail-closed default.
    session.add(models.BrokerTradingControl(id=1, enabled=True, updated_by=7))
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()




def test_live_trading_switch_defaults_off_and_blocks_order(monkeypatch, db_session):
    db_session.query(models.BrokerTradingControl).delete()
    db_session.commit()
    gateway_calls = []
    monkeypatch.setattr(
        broker_orders, "_gateway_request",
        lambda *args, **kwargs: gateway_calls.append(args) or {"success": True, "order_id": "MUST-NOT-SEND"},
    )

    state = broker_orders.get_trading_control(
        db=db_session, current_user=SimpleNamespace(id=7)
    )
    assert state["enabled"] is False

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload("blocked-while-off"), db=db_session,
            current_user=SimpleNamespace(id=7),
        )
    assert error.value.status_code == 403
    assert gateway_calls == []
    assert db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=7, client_id="blocked-while-off"
    ).count() == 0


def test_admin_trading_switch_can_be_turned_on_and_off(db_session):
    admin = SimpleNamespace(id=7)
    enabled = broker_orders.update_trading_control(
        broker_orders.BrokerTradingControlUpdate(enabled=True),
        db=db_session, current_user=admin,
    )
    assert enabled["enabled"] is True

    disabled = broker_orders.update_trading_control(
        broker_orders.BrokerTradingControlUpdate(enabled=False),
        db=db_session, current_user=admin,
    )
    assert disabled["enabled"] is False

def request_payload(client_id=None, investment_id=None):
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
        investment_id=investment_id,
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
    assert captured["transaction_type"] == "BUY"
    assert captured["tradingsymbol"] == "RELIANCE-EQ"
    assert captured["product"] == "CNC"
    assert captured["ref_price"] == "1450.00"


def test_each_order_gets_a_unique_client_id_when_not_supplied(monkeypatch, db_session):
    client_ids = []

    def fake_gateway(path, method, payload):
        client_ids.append(payload["client_id"])
        return {"success": True, "order_id": f"ORD-{len(client_ids)}"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    user = SimpleNamespace(id=7)

    broker_orders.place_broker_order(request_payload(), db=db_session, current_user=user)
    broker_orders.place_broker_order(request_payload(), db=db_session, current_user=user)

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
    broker_orders.place_broker_order(request_payload(), db=db_session, current_user=SimpleNamespace(id=7))

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
            request_payload(), db=db_session, current_user=SimpleNamespace(id=7)
        )

    assert error.value.status_code == 502


def test_ambiguous_gateway_response_requires_order_book_check(monkeypatch, db_session):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: {"message": "received"}
    )

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(), db=db_session, current_user=SimpleNamespace(id=7)
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


def test_admin_user_id_keeps_admin_access_after_email_change(monkeypatch):
    from app.routes.auth import get_current_admin

    admin = SimpleNamespace(id=7, email="new-admin@example.com")
    monkeypatch.setenv("ADMIN_USER_ID", "7")
    monkeypatch.setenv("ADMIN_EMAIL", "old-admin@example.com")

    assert get_current_admin(admin) is admin


def test_admin_user_id_does_not_grant_access_to_other_users(monkeypatch):
    from app.routes.auth import get_current_admin

    monkeypatch.setenv("ADMIN_USER_ID", "7")
    monkeypatch.setenv("ADMIN_EMAIL", "other@example.com")

    with pytest.raises(HTTPException) as error:
        get_current_admin(SimpleNamespace(id=8, email="other@example.com"))
    assert error.value.status_code == 403


def test_invalid_admin_user_id_fails_closed(monkeypatch):
    from app.routes.auth import get_current_admin

    monkeypatch.setenv("ADMIN_USER_ID", "not-a-number")
    with pytest.raises(HTTPException) as error:
        get_current_admin(SimpleNamespace(id=7, email="admin@example.com"))
    assert error.value.status_code == 503


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


def test_simultaneous_duplicate_requests_only_reach_gateway_once(monkeypatch, db_session):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from sqlalchemy.orm import Session

    engine = db_session.get_bind()
    user = SimpleNamespace(id=79)
    entered_gateway = Event()
    release_gateway = Event()
    calls = []

    def fake_gateway(path, method, payload):
        calls.append(payload["client_id"])
        entered_gateway.set()
        assert release_gateway.wait(timeout=5)
        return {"success": True, "order_id": "ORD-CONCURRENT"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)

    def submit():
        session = Session(bind=engine, expire_on_commit=False)
        try:
            return broker_orders.place_broker_order(
                request_payload("concurrent-key-1"), db=session, current_user=user
            )
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submit)
        assert entered_gateway.wait(timeout=5)
        second = pool.submit(submit)
        try:
            with pytest.raises(HTTPException) as error:
                second.result(timeout=5)
            assert error.value.status_code == 409
        finally:
            release_gateway.set()
        assert first.result(timeout=5)["order_id"] == "ORD-CONCURRENT"

    assert calls == ["concurrent-key-1"]



def test_ambiguous_gateway_exception_keeps_reservation_and_blocks_retry(monkeypatch, db_session):
    calls = []

    def gateway_times_out(path, method, payload):
        calls.append(payload["client_id"])
        raise TimeoutError("simulated timeout after request transmission")

    monkeypatch.setattr(broker_orders, "_gateway_request", gateway_times_out)
    user = SimpleNamespace(id=81)
    client_id = "ambiguous-timeout-key-1"

    with pytest.raises(TimeoutError):
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id, client_id=client_id
    ).one()
    assert reservation.status == "SUBMITTING"

    # A fresh session models a backend restart. The request must fail closed
    # rather than submit a potentially already-accepted broker order again.
    from sqlalchemy.orm import Session
    restarted_session = Session(bind=db_session.get_bind(), expire_on_commit=False)
    try:
        with pytest.raises(HTTPException) as duplicate:
            broker_orders.place_broker_order(
                request_payload(client_id),
                db=restarted_session,
                current_user=user,
            )
        assert duplicate.value.status_code == 409
    finally:
        restarted_session.close()

    assert calls == [client_id]



def _create_investments_table(db_session):
    db_session.execute(text("""
        CREATE TABLE investments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            symbol VARCHAR(100),
            quantity NUMERIC(18,6) NOT NULL DEFAULT 0
        )
    """))
    db_session.commit()


def test_selected_investment_is_validated_and_persisted(monkeypatch, db_session):
    _create_investments_table(db_session)
    db_session.execute(text("""
        INSERT INTO investments (id, user_id, name, symbol, quantity)
        VALUES (501, 7, 'Reliance', 'RELIANCE-EQ', 0)
    """))
    db_session.commit()
    monkeypatch.setattr(
        broker_orders, "_gateway_request",
        lambda *args, **kwargs: {"success": True, "order_id": "ORD-INVESTMENT"},
    )

    result = broker_orders.place_broker_order(
        request_payload("investment-link-1", investment_id=501),
        db=db_session,
        current_user=SimpleNamespace(id=7),
    )

    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=7, client_id="investment-link-1"
    ).one()
    assert result["order_id"] == "ORD-INVESTMENT"
    assert reservation.investment_id == 501


def test_cannot_submit_order_for_another_users_investment(monkeypatch, db_session):
    _create_investments_table(db_session)
    db_session.execute(text("""
        INSERT INTO investments (id, user_id, name, symbol, quantity)
        VALUES (502, 999, 'Private holding', 'PRIVATE', 1)
    """))
    db_session.commit()
    gateway_calls = []
    monkeypatch.setattr(
        broker_orders, "_gateway_request",
        lambda *args, **kwargs: gateway_calls.append(args) or {"success": True, "order_id": "SHOULD-NOT-SEND"},
    )

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload("wrong-owner-investment", investment_id=502),
            db=db_session,
            current_user=SimpleNamespace(id=7),
        )

    assert error.value.status_code == 404
    assert gateway_calls == []
    assert db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=7, client_id="wrong-owner-investment"
    ).count() == 0


def test_order_id_without_positive_acknowledgement_is_not_accepted(monkeypatch, db_session):
    # A broker may issue an ID even when the order is not accepted. The ID
    # alone must not move the reservation to ACKNOWLEDGED.
    monkeypatch.setattr(
        broker_orders, "_gateway_request",
        lambda *args, **kwargs: {"data": {"order_id": "ORD-AMBIGUOUS"}},
    )
    user = SimpleNamespace(id=84)
    client_id = "order-id-without-ack-1"

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    assert error.value.status_code == 502
    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id, client_id=client_id
    ).one()
    assert reservation.status == "SUBMITTING"
    assert reservation.gateway_order_id is None


@pytest.mark.parametrize(
    "gateway_result",
    [
        {"success": True, "order_id": "ORD-ERROR", "error": "Rejected by broker"},
        {"status": "success", "data": {"order_id": "ORD-ERROR", "error_code": "ORDER_REJECTED"}},
    ],
)
def test_http_200_error_envelope_is_not_accepted_even_with_order_id(
    monkeypatch, gateway_result, db_session
):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: gateway_result
    )
    user = SimpleNamespace(id=85)

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(), db=db_session, current_user=user
        )

    assert error.value.status_code == 502
    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id
    ).one()
    assert reservation.status == "REJECTED"
    assert reservation.gateway_order_id is None


@pytest.mark.parametrize(
    "gateway_result",
    [
        {"success": True, "order_id": "ORD-FALSE-ERROR", "error": False, "error_code": 0},
        {"status": "accepted", "order_id": "ORD-NULL-ERROR", "error": None, "errorCode": "0"},
    ],
)
def test_false_or_empty_gateway_error_fields_do_not_override_positive_ack(
    monkeypatch, gateway_result, db_session
):
    monkeypatch.setattr(
        broker_orders, "_gateway_request", lambda *args, **kwargs: gateway_result
    )
    user = SimpleNamespace(id=86)
    result = broker_orders.place_broker_order(
        request_payload(f"false-error-flag-{gateway_result['order_id']}"),
        db=db_session,
        current_user=user,
    )
    assert result["order_id"] == gateway_result["order_id"]
    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id, client_id=f"false-error-flag-{gateway_result['order_id']}"
    ).one()
    assert reservation.status == "ACKNOWLEDGED"


def test_missing_reservation_table_fails_closed_without_runtime_ddl(monkeypatch, db_session):
    """Missing schema must block submission; request handlers must not run DDL."""
    engine = db_session.get_bind()
    db_session.close()
    models.BrokerOrderSubmission.__table__.drop(bind=engine, checkfirst=True)
    calls = []
    monkeypatch.setattr(
        broker_orders, "_gateway_request",
        lambda *args, **kwargs: calls.append(args) or {"success": True, "order_id": "MUST-NOT-SEND"},
    )
    from sqlalchemy.orm import Session
    session = Session(bind=engine, expire_on_commit=False)
    try:
        with pytest.raises(HTTPException) as error:
            broker_orders.place_broker_order(
                request_payload("missing-table-fail-closed-1"),
                db=session,
                current_user=SimpleNamespace(id=7),
            )
        assert error.value.status_code == 503
        assert calls == []
    finally:
        session.close()


def _configure_real_gateway_http_error_test(monkeypatch):
    import io
    from urllib.error import HTTPError

    monkeypatch.setattr(broker_orders, "GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(broker_orders, "GATEWAY_SECRET", "test-secret")
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        raise HTTPError(
            request.full_url, 400, "Bad Request", {},
            io.BytesIO(
                b'[{"status":"error","message":"Invalid symbol. Scrip Name not found in exchange file.",'
                b'"error_type":"InputException","data":null}]'
            ),
        )

    monkeypatch.setattr(broker_orders, "urlopen", fake_urlopen)
    return calls


def test_gateway_http_400_json_list_persists_definite_rejection(monkeypatch, db_session):
    import json

    calls = _configure_real_gateway_http_error_test(monkeypatch)
    user = SimpleNamespace(id=91)
    client_id = "gateway-400-list-rejection"

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    assert error.value.status_code == 502
    assert "Invalid symbol" in error.value.detail
    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id, client_id=client_id
    ).one()
    assert reservation.status == "REJECTED"
    stored_response = json.loads(reservation.response_json)
    assert "Invalid symbol" in stored_response["detail"]
    assert stored_response["gateway_http_status"] == 400
    assert len(calls) == 1


def test_gateway_http_409_keeps_reservation_submitting(monkeypatch, db_session):
    import io
    from urllib.error import HTTPError

    monkeypatch.setattr(broker_orders, "GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(broker_orders, "GATEWAY_SECRET", "test-secret")
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)
        raise HTTPError(
            request.full_url, 409, "Conflict", {},
            io.BytesIO(b'{"message":"Duplicate client_id; order may already exist"}'),
        )

    monkeypatch.setattr(broker_orders, "urlopen", fake_urlopen)
    user = SimpleNamespace(id=92)
    client_id = "gateway-409-ambiguous"

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    assert error.value.status_code == 502
    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id, client_id=client_id
    ).one()
    assert reservation.status == "SUBMITTING"
    assert reservation.response_json in (None, "")
    assert len(calls) == 1


@pytest.mark.parametrize("gateway_status", [500, 503])
def test_gateway_http_5xx_keeps_reservation_submitting(
    monkeypatch, db_session, gateway_status
):
    import io
    from urllib.error import HTTPError

    monkeypatch.setattr(broker_orders, "GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(broker_orders, "GATEWAY_SECRET", "test-secret")

    def fake_urlopen(request, timeout):
        raise HTTPError(
            request.full_url, gateway_status, "Gateway Error", {},
            io.BytesIO(b'{"message":"upstream error"}'),
        )

    monkeypatch.setattr(broker_orders, "urlopen", fake_urlopen)
    user = SimpleNamespace(id=93)
    client_id = f"gateway-{gateway_status}-ambiguous"

    with pytest.raises(HTTPException) as error:
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    assert error.value.status_code == 502
    reservation = db_session.query(models.BrokerOrderSubmission).filter_by(
        user_id=user.id, client_id=client_id
    ).one()
    assert reservation.status == "SUBMITTING"


def test_acknowledgement_commit_failure_keeps_durable_reservation_and_blocks_retry(
    monkeypatch, db_session
):
    """A broker ack followed by a DB commit error must never trigger blind resubmission."""
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    gateway_calls = []

    def fake_gateway(path, method, payload):
        gateway_calls.append(payload["client_id"])
        return {"success": True, "order_id": "MOCK-ACK-PERSISTENCE"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    user = SimpleNamespace(id=97)
    client_id = "ack-persistence-commit-failure"

    # Allow the initial SUBMITTING reservation commit, but fail the final
    # commit that would persist ACKNOWLEDGED. This simulates a failure before
    # the database confirms that final state was committed.
    original_commit = db_session.commit
    commit_calls = 0

    def fail_acknowledgement_commit():
        nonlocal commit_calls
        commit_calls += 1
        if commit_calls == 2:
            raise SQLAlchemyError("simulated acknowledgement commit failure")
        return original_commit()

    monkeypatch.setattr(db_session, "commit", fail_acknowledgement_commit)

    with pytest.raises(SQLAlchemyError, match="simulated acknowledgement commit failure"):
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    # Roll back the failed ORM transaction and inspect persisted state from a
    # new session, not the possibly stale in-memory reservation object.
    db_session.rollback()
    engine = db_session.get_bind()
    with Session(bind=engine, expire_on_commit=False) as verification_session:
        reservation = verification_session.query(models.BrokerOrderSubmission).filter_by(
            user_id=user.id, client_id=client_id
        ).one()
        assert reservation.status == "SUBMITTING"
        assert reservation.gateway_order_id is None

    # A retry with the same durable idempotency key is blocked before gateway I/O.
    with Session(bind=engine, expire_on_commit=False) as retry_session:
        with pytest.raises(HTTPException) as duplicate:
            broker_orders.place_broker_order(
                request_payload(client_id),
                db=retry_session,
                current_user=user,
            )
        assert duplicate.value.status_code == 409

    assert gateway_calls == [client_id]



def test_acknowledgement_commit_succeeds_but_confirmation_is_lost_blocks_retry(
    monkeypatch, db_session
):
    """If commit lands but its confirmation is lost, retry must not resubmit."""
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    gateway_calls = []

    def fake_gateway(path, method, payload):
        gateway_calls.append(payload["client_id"])
        return {"success": True, "order_id": "MOCK-COMMIT-UNCERTAINTY"}

    monkeypatch.setattr(broker_orders, "_gateway_request", fake_gateway)
    user = SimpleNamespace(id=98)
    client_id = "ack-commit-outcome-uncertain"

    original_commit = db_session.commit
    commit_calls = 0

    def commit_then_lose_confirmation():
        nonlocal commit_calls
        commit_calls += 1
        if commit_calls == 2:
            # Simulate the database committing ACKNOWLEDGED, while the caller
            # receives an exception before learning that the commit succeeded.
            original_commit()
            raise SQLAlchemyError("simulated lost commit confirmation")
        return original_commit()

    monkeypatch.setattr(db_session, "commit", commit_then_lose_confirmation)

    with pytest.raises(SQLAlchemyError, match="simulated lost commit confirmation"):
        broker_orders.place_broker_order(
            request_payload(client_id), db=db_session, current_user=user
        )

    # Do not assume rollback means the remote commit was undone: inspect the
    # durable result through a separate session.
    db_session.rollback()
    engine = db_session.get_bind()
    with Session(bind=engine, expire_on_commit=False) as verification_session:
        reservation = verification_session.query(models.BrokerOrderSubmission).filter_by(
            user_id=user.id, client_id=client_id
        ).one()
        assert reservation.status == "ACKNOWLEDGED"
        assert reservation.gateway_order_id == "MOCK-COMMIT-UNCERTAINTY"

    # A repeated request must be rejected using the durable idempotency key,
    # regardless of the first caller's uncertainty about the commit result.
    with Session(bind=engine, expire_on_commit=False) as retry_session:
        with pytest.raises(HTTPException) as duplicate:
            broker_orders.place_broker_order(
                request_payload(client_id), db=retry_session, current_user=user
            )
        assert duplicate.value.status_code == 409

    assert gateway_calls == [client_id]
