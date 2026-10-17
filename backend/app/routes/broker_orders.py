"""Authenticated m.Stock broker-order proxy.

Gateway contract:
  POST /order          -> broker order placement
  GET  /orders         -> broker order book
  GET  /trades         -> executed trade book enriched with client_reference
The gateway owns m.Stock credentials and must validate product/validity/order fields.
This API never records a holding from order placement alone; confirmed-fill reconciliation
must be implemented separately before updating portfolio quantities.
"""
import json
import logging
import os
from uuid import uuid4
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.routes.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/broker-orders", tags=["Broker Orders"])
logger = logging.getLogger(__name__)
GATEWAY_URL = os.getenv("MSTOCK_GATEWAY_URL", "http://54.153.201.74:8000").rstrip("/")
GATEWAY_ORDER_PLACE_PATH = os.getenv("MSTOCK_GATEWAY_ORDER_PLACE_PATH", "/order")
GATEWAY_ORDER_BOOK_PATH = os.getenv("MSTOCK_GATEWAY_ORDER_BOOK_PATH", "/orders")
GATEWAY_TIMEOUT_SECONDS = 15


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

    @model_validator(mode="after")
    def validate_order(self):
        self.side = self.side.strip().upper()
        self.symbol = self.symbol.strip().upper()
        self.exchange = self.exchange.strip().upper()
        self.product_type = self.product_type.strip().upper()
        self.order_type = self.order_type.strip().upper()
        self.validity = self.validity.strip().upper()
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
    url = f"{GATEWAY_URL}{path}"
    if query:
        url += "?" + urlencode(query)
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Financial-OS/1.0",
    }
    # Optional shared secret for gateway deployments that enforce it. Keep the
    # secret in environment configuration, never in source control.
    gateway_secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if gateway_secret:
        # Never transmit the shared gateway secret over plaintext HTTP.
        # Configure HTTPS (or a private encrypted tunnel) before enabling it.
        from urllib.parse import urlparse
        if urlparse(url).scheme.lower() != "https":
            raise HTTPException(
                status_code=503,
                detail="MSTOCK_GATEWAY_SECRET is configured, but the gateway URL is not HTTPS. Configure HTTPS before using the shared secret.",
            )
        headers["X-Financial-OS-Gateway-Secret"] = gateway_secret
    request = Request(url, data=body, method=method, headers=headers)
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
            message = detail.get("detail") or detail.get("message") or detail.get("error")
        except Exception:
            message = None
        if exc.code == 404:
            raise HTTPException(status_code=503, detail="The AWS m.Stock gateway does not yet implement this order endpoint.") from exc
        raise HTTPException(status_code=502, detail=message or f"m.Stock gateway returned HTTP {exc.code}.") from exc
    except URLError as exc:
        logger.warning("m.Stock order gateway connection failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Unable to connect to the AWS m.Stock gateway.") from exc
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("m.Stock order gateway response failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Gateway timed out or returned invalid JSON; check broker order status before retrying.") from exc


@router.post("/", status_code=202)
def place_broker_order(request: BrokerOrderRequest, current_user: User = Depends(get_current_user)):
    """Submit a real broker order. The AWS gateway handles broker authentication."""
    client_reference = f"financial-os-{current_user.id}-{uuid4().hex}"
    # Translate the Financial OS API model into the field names accepted by the
    # existing Flask gateway. client_id is persisted in gateway order logs and
    # later joined to executed trade-book rows by broker order ID.
    payload = {
        "client_id": client_reference,
        "tradingsymbol": request.symbol,
        "exchange": request.exchange,
        "transaction_type": request.side,
        "order_type": request.order_type,
        "product": "CNC" if request.product_type == "DELIVERY" else "MIS",
        "validity": request.validity,
        "quantity": request.quantity,
        "price": str(request.price),
        "ref_price": str(request.quote_price),
        "trigger_price": "0",
        "tag": "fos",
    }
    result = _gateway_request(GATEWAY_ORDER_PLACE_PATH, "POST", payload)
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
    if result.get("success") is False or nested_data.get("success") is False or any(
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
        raise HTTPException(status_code=502, detail=message)

    order_id = (
        result.get("order_id")
        or result.get("orderid")
        or nested_data.get("order_id")
        or nested_data.get("orderid")
    )
    # Only say "accepted" when the gateway provides a positive acknowledgement.
    # A generic/empty response must not be presented as a successful order.
    accepted_statuses = {"success", "accepted", "open", "pending", "submitted", "complete", "completed"}
    explicitly_accepted = (
        result.get("success") is True
        or nested_data.get("success") is True
        or any(
            isinstance(status, str) and status.strip().lower() in accepted_statuses
            for status in status_values
        )
        or bool(order_id)
    )
    if not explicitly_accepted:
        logger.warning("m.Stock gateway returned an ambiguous placement response for user %s", current_user.id)
        raise HTTPException(
            status_code=502,
            detail="The gateway response did not confirm whether the order was accepted. Check the broker order book before retrying.",
        )

    return {
        "status": "submitted",
        "client_reference": client_reference,
        "user_id": current_user.id,
        "order_id": order_id,
        "broker_response": result,
        "portfolio_updated": False,
        "message": "The broker acknowledged the order request. This does not confirm execution; holdings update only after confirmed fills are reconciled.",
    }


@router.get("/")
def list_broker_orders(current_user: User = Depends(get_current_user), status: str | None = Query(default=None, max_length=30)):
    """Read broker order book; the gateway must return orders belonging to its configured account."""
    query = {"status": status} if status else None
    result = _gateway_request(GATEWAY_ORDER_BOOK_PATH, "GET", query=query)
    return {"status": "success", "user_id": current_user.id, "broker_response": result}
