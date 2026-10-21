"""Authenticated m.Stock broker-order proxy.

Gateway contract:
  POST /order         -> broker order placement
  GET  /orders        -> broker order book (optional user-independent account book)
The gateway owns m.Stock credentials and must validate product/validity/order fields.
This API never records a holding from order placement alone; confirmed-fill reconciliation
must be implemented separately before updating portfolio quantities.
"""
import json
import hashlib
import logging
import os
from uuid import uuid4
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, model_validator

from app.routes.auth import get_current_user, get_current_admin
from app.models import User, BrokerOrderSubmission, BrokerTradingControl
from app.database.database import get_db

router = APIRouter(prefix="/api/broker-orders", tags=["Broker Orders"])
logger = logging.getLogger(__name__)


class DefiniteGatewayRejection(HTTPException):
    """Gateway response proves the order request was rejected before acceptance."""

    definite_rejection = True

    def __init__(self, detail: str, gateway_status: int):
        super().__init__(status_code=502, detail=detail)
        self.gateway_status = gateway_status
GATEWAY_URL = os.getenv("MSTOCK_GATEWAY_URL", "").rstrip("/")
GATEWAY_SECRET = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
GATEWAY_ORDER_PLACE_PATH = os.getenv("MSTOCK_GATEWAY_ORDER_PLACE_PATH", "/order")
GATEWAY_ORDER_BOOK_PATH = os.getenv("MSTOCK_GATEWAY_ORDER_BOOK_PATH", "/orders")
GATEWAY_TIMEOUT_SECONDS = 15


class BrokerTradingControlUpdate(BaseModel):
    enabled: bool


class BrokerOrderRequest(BaseModel):
    side: str
    symbol: str = Field(min_length=1, max_length=80)
    exchange: str
    product_type: str
    order_type: str
    validity: str
    quantity: int = Field(gt=0, le=1000000)
    price: Decimal = Field(default=Decimal("0"), ge=0)
    quote_price: Decimal = Field(gt=0)
    client_id: str | None = Field(default=None, min_length=1, max_length=120)
    investment_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_order(self):
        self.side = self.side.strip().upper()
        self.symbol = self.symbol.strip().upper()
        self.exchange = self.exchange.strip().upper()
        self.product_type = self.product_type.strip().upper()
        self.order_type = self.order_type.strip().upper()
        self.validity = self.validity.strip().upper()
        if self.client_id is not None:
            self.client_id = self.client_id.strip()
            if not self.client_id:
                raise ValueError("client_id must not be blank")
        if self.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if self.exchange not in {"NSE", "BSE"}:
            raise ValueError("exchange must be NSE or BSE")
        if self.product_type not in {"DELIVERY", "INTRADAY"}:
            raise ValueError("product_type must be DELIVERY or INTRADAY")
        if self.order_type not in {"MARKET", "LIMIT"}:
            raise ValueError("order_type must be MARKET or LIMIT")
        if self.validity not in {"DAY", "IOC"}:
            raise ValueError("validity must be DAY or IOC")
        if self.order_type == "LIMIT" and self.price <= 0:
            raise ValueError("A positive limit price is required for LIMIT orders")
        if self.order_type == "MARKET":
            self.price = Decimal("0")
        return self


def _gateway_request(path: str, method: str, payload: dict | None = None, query: dict | None = None):
    if not GATEWAY_URL:
        raise HTTPException(status_code=503, detail="MSTOCK_GATEWAY_URL is not configured.")
    # Broker credentials are shared by the configured m.Stock account. Keep
    # the secret on loopback only; never send it to a public IP over HTTP.
    if GATEWAY_URL not in {"http://127.0.0.1:8000", "http://localhost:8000"}:
        raise HTTPException(
            status_code=503,
            detail="Broker gateway must be configured on loopback HTTP (127.0.0.1:8000).",
        )
    if not GATEWAY_SECRET:
        raise HTTPException(status_code=503, detail="MSTOCK_GATEWAY_SECRET is not configured; broker gateway requests are disabled.")
    url = f"{GATEWAY_URL}{path}"
    if query:
        url += "?" + urlencode(query)
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=body, method=method, headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Financial-OS/1.0",
        "X-Financial-OS-Gateway-Secret": GATEWAY_SECRET,
    })
    try:
        with urlopen(request, timeout=GATEWAY_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, dict):
                raise HTTPException(status_code=502, detail="Gateway returned an invalid order response.")
            if response.status >= 400:
                raise HTTPException(status_code=502, detail="Gateway rejected the order request.")
            return data
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
            if isinstance(detail, list):
                detail = detail[0] if detail else {}
            if not isinstance(detail, dict):
                detail = {}
            message = detail.get("detail") or detail.get("message") or detail.get("error")
        except Exception:
            message = None
        if exc.code == 404:
            raise HTTPException(status_code=503, detail="The AWS m.Stock gateway does not yet implement this order endpoint.") from exc
        message = message or f"m.Stock gateway returned HTTP {exc.code}."
        # Keep the public response at 502, but preserve whether the gateway's
        # 400/422 response proves this order request was rejected. A 409 may
        # indicate a duplicate of an order already sent, so it stays ambiguous.
        if exc.code in (400, 422):
            raise DefiniteGatewayRejection(detail=message, gateway_status=exc.code) from exc
        raise HTTPException(status_code=502, detail=message) from exc
    except URLError as exc:
        logger.warning("m.Stock order gateway connection failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Unable to connect to the AWS m.Stock gateway.") from exc
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("m.Stock order gateway response failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Gateway timed out or returned invalid JSON; check broker order status before retrying.") from exc


@router.get("/trading-control")
def get_trading_control(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Return the persistent Financial OS live-order switch; absent setting is OFF."""
    try:
        control = db.query(BrokerTradingControl).filter_by(id=1).first()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Trading control storage is unavailable; live orders remain blocked.") from exc
    return {
        "enabled": bool(control.enabled) if control else False,
        "updated_at": control.updated_at.isoformat() if control and control.updated_at else None,
    }


@router.put("/trading-control")
def update_trading_control(
    request: BrokerTradingControlUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Change the Financial OS live-order switch. Disabling blocks new orders only."""
    try:
        control = db.query(BrokerTradingControl).filter_by(id=1).first()
        if control is None:
            control = BrokerTradingControl(id=1, enabled=request.enabled, updated_by=current_user.id)
            db.add(control)
        else:
            control.enabled = request.enabled
            control.updated_by = current_user.id
        db.commit()
        db.refresh(control)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Unable to save trading control; live-order state was not changed.") from exc
    return {
        "enabled": bool(control.enabled),
        "updated_at": control.updated_at.isoformat() if control.updated_at else None,
    }


@router.post("/", status_code=202)
def place_broker_order(request: BrokerOrderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    """Submit a real-money order only for the configured platform owner."""
    # The persistent kill switch defaults to OFF when no row exists. It is
    # checked before investment validation, reservation creation, or gateway I/O.
    try:
        trading_control = db.query(BrokerTradingControl).filter_by(id=1).first()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Trading control storage is unavailable; order was not submitted.") from exc
    if trading_control is None or not trading_control.enabled:
        raise HTTPException(status_code=403, detail="Live trading is OFF. Turn it ON in Settings > Live Trading before submitting new orders.")
    # Keep the API's canonical fields and also provide the field names used
    # by the deployed Flask gateway. This makes the contract explicit while
    # remaining compatible with existing backend callers.
    # When an investment is selected, validate ownership before reserving or
    # sending any order. The investment table is created by the investments API.
    if request.investment_id is not None:
        try:
            owned_investment = db.execute(text("""
                SELECT id FROM investments
                WHERE id = :investment_id AND user_id = :user_id
            """), {"investment_id": request.investment_id, "user_id": current_user.id}).first()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(status_code=503, detail="Unable to validate the selected investment; order was not submitted.") from exc
        if owned_investment is None:
            raise HTTPException(status_code=404, detail="Selected investment was not found for this user.")

    gateway_product = {"DELIVERY": "CNC", "INTRADAY": "MIS"}[request.product_type]
    payload = {
        "side": request.side,
        "symbol": request.symbol,
        "exchange": request.exchange,
        "product_type": request.product_type,
        "order_type": request.order_type,
        "validity": request.validity,
        "quantity": request.quantity,
        "price": str(request.price),
        "quote_price": str(request.quote_price),
        # AWS gateway's current contract uses m.Stock field names.
        "transaction_type": request.side,
        "tradingsymbol": request.symbol,
        "product": gateway_product,
        "ref_price": str(request.quote_price),
        # Reuse the caller-provided ID for retries of the same form submission.
        # Both backend DB reservation and gateway guard use this ID.
        "client_id": request.client_id or f"financial-os-{current_user.id}-{uuid4().hex}",
    }
    # Commit a durable reservation before the external side effect. The DB
    # unique constraint arbitrates concurrent requests across backend workers.
    # Existing IDs are never automatically resubmitted, including after restart.
    canonical_payload = json.dumps(
        {key: value for key, value in payload.items() if key != "client_id"},
        sort_keys=True,
        separators=(",", ":"),
    )
    # Investment selection is backend metadata, not a broker API field, but
    # it is included in the idempotency hash so one client_id cannot be rebound.
    canonical_payload = json.dumps(
        {"order": json.loads(canonical_payload), "investment_id": request.investment_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    payload_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    reservation = BrokerOrderSubmission(
        user_id=current_user.id,
        investment_id=request.investment_id,
        symbol=request.symbol,
        exchange=request.exchange,
        side=request.side,
        quantity=request.quantity,
        client_id=payload["client_id"],
        payload_hash=payload_hash,
        status="SUBMITTING",
    )
    try:
        # Schema creation belongs in an explicit migration/startup step, never
        # in a live order request. Runtime DDL can fail for an application DB role
        # that correctly has DML privileges but no CREATE privilege, preventing
        # every order reservation before any broker request is sent.
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
    except IntegrityError as exc:
        db.rollback()
        existing = db.query(BrokerOrderSubmission).filter(
            BrokerOrderSubmission.user_id == current_user.id,
            BrokerOrderSubmission.client_id == payload["client_id"],
        ).first()
        if existing:
            if existing.payload_hash != payload_hash:
                raise HTTPException(status_code=409, detail="This client_id was already used for a different order.") from exc
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate order blocked. Existing request status: {existing.status}. Verify order status directly with the broker before taking further action.",
            ) from exc
        raise HTTPException(status_code=503, detail="Unable to verify order idempotency state; order was not submitted.") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        # Keep the full traceback and SQLAlchemy exception class in the service
        # log; never log SQL parameters or connection strings (they may contain secrets).
        logger.error(
            "Broker order reservation failed (exception_type=%s)",
            type(exc).__name__,
            exc_info=True,
        )
        raise HTTPException(status_code=503, detail="Order submission is disabled because durable duplicate protection is unavailable.") from exc

    try:
        result = _gateway_request(GATEWAY_ORDER_PLACE_PATH, "POST", payload)
    except HTTPException as exc:
        # Explicit HTTP 4xx responses are definite gateway rejections. Keep
        # timeouts and 5xx responses SUBMITTING because acceptance is ambiguous.
        if getattr(exc, "definite_rejection", False) or 400 <= exc.status_code < 500:
            reservation.status = "REJECTED"
            reservation.response_json = json.dumps(
                {
                    "http_status": exc.status_code,
                    "gateway_http_status": getattr(exc, "gateway_status", None),
                    "detail": exc.detail,
                },
                default=str,
            )
            db.commit()
        raise
    except Exception:
        # A timeout may occur after broker acceptance. Keep the durable
        # SUBMITTING reservation and require reconciliation; never retry blindly.
        raise
    nested_data = result.get("data") if isinstance(result.get("data"), dict) else {}
    # Broker gateways may wrap the placement result inside "data". Treat an
    # explicit rejection anywhere in that response as a rejection, not success.
    status_values = [
        result.get("status"),
        nested_data.get("status"),
        result.get("order_status"),
        nested_data.get("order_status"),
    ]
    rejected_statuses = {"error", "failed", "failure", "rejected", "not_accepted"}
    # A broker may return HTTP 200 and still include an error envelope or a
    # rejection code. Never let an order_id alone override an explicit error.
    error_values = [
        result.get("error"), result.get("error_code"), result.get("errorCode"),
        nested_data.get("error"), nested_data.get("error_code"), nested_data.get("errorCode"),
    ]
    def is_error_value(value):
        # Some gateway wrappers always include error/error_code keys and use
        # false, null, or zero to mean no error. Do not reject those responses.
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, str) and value.strip().lower() in {"", "0", "false", "none", "null"}:
            return False
        return True

    has_error = any(is_error_value(value) for value in error_values)
    if has_error or result.get("success") is False or nested_data.get("success") is False or any(
        isinstance(status, str) and status.strip().lower() in rejected_statuses
        for status in status_values
    ):
        message = (
            nested_data.get("message")
            or result.get("message")
            or nested_data.get("error")
            or result.get("error")
            or "Gateway did not accept the order."
        )
        reservation.status = "REJECTED"
        reservation.response_json = json.dumps(result, default=str)
        db.commit()
        raise HTTPException(status_code=502, detail=message)

    order_id = (
        result.get("order_id")
        or result.get("orderid")
        or nested_data.get("order_id")
        or nested_data.get("orderid")
    )
    # A broker order ID alone is not proof of acceptance: rejected orders may
    # still receive an ID. Require both an identifier and a positive status.
    # Missing/ambiguous acknowledgements stay SUBMITTING for manual reconciliation
    # and are never automatically resubmitted.
    accepted_statuses = {"success", "accepted", "open", "pending", "submitted", "complete", "completed"}
    positive_ack = (
        result.get("success") is True
        or nested_data.get("success") is True
        or any(
            isinstance(status, str) and status.strip().lower() in accepted_statuses
            for status in status_values
        )
    )
    if not order_id or not positive_ack:
        # Preserve acknowledgement evidence. Do not mark this rejected: the
        # broker may have accepted the order despite an incomplete response.
        reservation.response_json = json.dumps(result, default=str)
        db.commit()
        logger.warning("m.Stock gateway returned an ambiguous placement response for user %s", current_user.id)
        raise HTTPException(
            status_code=502,
            detail="The gateway response did not confirm acceptance with a broker order ID. Check the broker order book and do not resubmit until order status is verified directly with the broker.",
        )

    reservation.status = "ACKNOWLEDGED"
    reservation.gateway_order_id = str(order_id)
    reservation.response_json = json.dumps(result, default=str)
    db.commit()

    return {
        "status": "submitted",
        "user_id": current_user.id,
        "order_id": order_id,
        "broker_response": result,
        "portfolio_updated": False,
        "message": "The broker acknowledged the order request. This does not confirm execution; holdings update only after confirmed fills are reconciled.",
    }


@router.get("/")
def list_broker_orders(current_user: User = Depends(get_current_admin), status: str | None = Query(default=None, max_length=30)):
    """Read broker order book; the gateway must return orders belonging to its configured account."""
    query = {"status": status} if status else None
    result = _gateway_request(GATEWAY_ORDER_BOOK_PATH, "GET", query=query)
    return {"status": "success", "user_id": current_user.id, "broker_response": result}
