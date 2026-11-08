"""Private Vercel service that adapts Financial OS gateway contracts to m.Stock Type-A APIs.

All routes are intended for internal service-to-service calls from the Financial OS API.
The shared gateway secret is checked on every request; broker orders remain protected
again by the Financial OS admin gate, persistent kill switch, and durable idempotency.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pyotp
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

API_BASE_URL = os.getenv("MSTOCK_API_BASE_URL", "https://api.mstock.trade").rstrip("/")
API_KEY = os.getenv("MSTOCK_API_KEY", "").strip()
GATEWAY_SECRET = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
TOTP_SECRET = os.getenv("MSTOCK_TOTP_SECRET", "").strip()
STATIC_ACCESS_TOKEN = os.getenv("MSTOCK_ACCESS_TOKEN", "").strip()
REQUEST_TIMEOUT_SECONDS = 15

_token_lock = threading.Lock()
_cached_access_token: str | None = None
_cached_token_expires_at: datetime | None = None

app = FastAPI(
    title="Financial OS m.Stock Gateway",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def require_gateway_secret(
    supplied: str | None = Header(default=None, alias="X-Financial-OS-Gateway-Secret"),
) -> None:
    expected = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        raise HTTPException(status_code=403, detail="Gateway authentication failed.")


def _now_ist() -> datetime:
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def _local_token_expiry() -> datetime:
    """Refresh before the earlier of the 12-hour token limit and midnight IST."""
    now = _now_ist()
    midnight = datetime.combine(
        now.date() + timedelta(days=1),
        datetime.min.time(),
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )
    return min(now + timedelta(hours=12), midnight) - timedelta(seconds=60)


def _generate_fresh_totp(secret: str, *, next_period: bool = False) -> str:
    """Generate TOTP away from a 30-second boundary to avoid sending an expiring code."""
    totp = pyotp.TOTP(secret)
    remaining = 30 - (int(time.time()) % 30)
    if next_period:
        time.sleep(remaining + 1)
    elif remaining < 5:
        time.sleep(remaining + 1)
    return totp.now()


def _post_totp_session(code: str) -> dict:
    body = urlencode({"api_key": API_KEY, "totp": code}).encode("utf-8")
    request = Request(
        f"{API_BASE_URL}/openapi/typea/session/verifytotp",
        data=body,
        method="POST",
        headers={
            "X-Mirae-Version": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {}
        if _is_totp_rejection(payload, exc.code):
            return payload
        if exc.code == 403:
            raise HTTPException(
                status_code=503,
                detail="m.Stock API key is invalid, expired, or suspended. Check the broker API subscription.",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail=f"m.Stock authentication service rejected the request (HTTP {exc.code}).",
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=503, detail="Unable to reach m.Stock authentication service.") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=502, detail="m.Stock authentication returned an invalid response.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="m.Stock authentication returned an invalid response.")
    return payload


def _is_totp_rejection(payload: dict, http_status: int | None = None) -> bool:
    if not isinstance(payload, dict):
        return False
    message = str(payload.get("message") or "").lower()
    error_type = str(payload.get("error_type") or "").lower()
    return (
        (http_status in {400, 401} or payload.get("status") == "error")
        and any(term in message or term in error_type for term in ("totp", "otp", "macm60", "ma400"))
    )


def _login_with_totp() -> str:
    if not API_KEY:
        raise HTTPException(status_code=503, detail="MSTOCK_API_KEY is not configured.")
    if not TOTP_SECRET:
        raise HTTPException(
            status_code=503,
            detail="MSTOCK_TOTP_SECRET is not configured; enable m.Stock Trading API TOTP.",
        )

    payload = _post_totp_session(_generate_fresh_totp(TOTP_SECRET))
    if _is_totp_rejection(payload):
        # A rejected code may have crossed a 30-second boundary in transit.
        # Wait for the next period and make exactly one fresh attempt.
        payload = _post_totp_session(_generate_fresh_totp(TOTP_SECRET, next_period=True))

    if payload.get("status") not in {"success", True}:
        if str(payload.get("error_type") or "").lower() in {"apikeyexception"}:
            raise HTTPException(
                status_code=503,
                detail="m.Stock API key is invalid, expired, or suspended. Check the broker API subscription.",
            )
        raise HTTPException(
            status_code=503,
            detail="m.Stock TOTP authentication failed. Verify the TOTP secret, account setting, and server clock.",
        )

    data = payload.get("data")
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token.strip():
        raise HTTPException(
            status_code=502,
            detail="m.Stock authentication response did not contain an access token.",
        )
    return token.strip()


def _get_access_token(force_refresh: bool = False) -> str:
    global _cached_access_token, _cached_token_expires_at

    if STATIC_ACCESS_TOKEN:
        if not API_KEY:
            raise HTTPException(status_code=503, detail="MSTOCK_API_KEY is not configured.")
        return STATIC_ACCESS_TOKEN

    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    if (
        not force_refresh
        and _cached_access_token
        and _cached_token_expires_at
        and now < _cached_token_expires_at
    ):
        return _cached_access_token

    with _token_lock:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        if (
            not force_refresh
            and _cached_access_token
            and _cached_token_expires_at
            and now < _cached_token_expires_at
        ):
            return _cached_access_token
        _cached_access_token = _login_with_totp()
        _cached_token_expires_at = _local_token_expiry()
        return _cached_access_token


def _mstock_request(
    path: str,
    method: str = "GET",
    *,
    params: dict | None = None,
    form: dict | None = None,
    raw: bool = False,
    retry_auth: bool = True,
    force_refresh: bool = False,
    allow_provider_error: bool = False,
):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="MSTOCK_API_KEY is not configured.")
    if not API_BASE_URL.startswith("https://"):
        raise HTTPException(status_code=503, detail="m.Stock API base URL must use HTTPS.")

    url = f"{API_BASE_URL}{path}"
    if params:
        url += "?" + urlencode(params, doseq=True)
    body = urlencode(form).encode("utf-8") if form is not None else None
    headers = {
        "X-Mirae-Version": "1",
        "Authorization": f"token {API_KEY}:{_get_access_token(force_refresh)}",
        "Accept": "application/json, text/csv",
    }
    if form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content = response.read()
    except HTTPError as exc:
        if exc.code == 401 and retry_auth and not STATIC_ACCESS_TOKEN:
            return _mstock_request(
                path, method, params=params, form=form, raw=raw,
                retry_auth=False, force_refresh=True,
                allow_provider_error=allow_provider_error,
            )
        if exc.code == 401:
            message = "m.Stock rejected the access token after one re-authentication attempt."
        elif exc.code == 403:
            message = "m.Stock API key is invalid, expired, or suspended. Check the broker API subscription."
        else:
            message = f"m.Stock API request failed (HTTP {exc.code})."
        raise HTTPException(status_code=502, detail=message) from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail="Unable to reach m.Stock API.") from exc

    if raw:
        return content

    try:
        payload = json.loads(content.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=502, detail="m.Stock API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="m.Stock API returned an invalid response.")
    if not allow_provider_error and payload.get("status") not in {"success", True}:
        raise HTTPException(
            status_code=502,
            detail=str(payload.get("message") or "m.Stock API returned an unsuccessful response."),
        )
    return payload


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Financial OS m.Stock Gateway",
        "authentication": "totp" if TOTP_SECRET else ("static-token" if STATIC_ACCESS_TOKEN else "not-configured"),
    }


@app.get("/quote", dependencies=[Depends(require_gateway_secret)])
def quote(symbol: str = Query(..., min_length=1, max_length=120)):
    cleaned = symbol.strip().upper()
    if not cleaned or ":" not in cleaned:
        raise HTTPException(status_code=400, detail="Use an exchange-qualified symbol such as NSE:RELIANCE-EQ.")
    payload = _mstock_request(
        "/openapi/typea/instruments/quote/ohlc",
        params={"i": cleaned},
    )
    data = payload.get("data")
    if not isinstance(data, dict) or cleaned not in data:
        raise HTTPException(status_code=502, detail="m.Stock did not return the requested quote.")
    return {"status": "success", "symbol": cleaned, "data": {cleaned: data[cleaned]}}


@app.get("/index-quote", dependencies=[Depends(require_gateway_secret)])
def index_quote(exchange: str, symbol: str):
    cleaned_exchange = exchange.strip().upper()
    cleaned_symbol = symbol.strip().upper()
    if cleaned_exchange not in {"NSE", "BSE"} or not cleaned_symbol:
        raise HTTPException(status_code=400, detail="A valid exchange and index symbol are required.")
    qualified = f"{cleaned_exchange}:{cleaned_symbol}"
    payload = _mstock_request(
        "/openapi/typea/instruments/quote/ohlc",
        params={"i": qualified},
    )
    data = payload.get("data")
    if not isinstance(data, dict) or qualified not in data:
        raise HTTPException(status_code=502, detail=f"m.Stock did not return {qualified}.")
    quote_data = data[qualified]
    return {"status": "success", "last_price": quote_data.get("last_price"), "data": {qualified: quote_data}}


@app.get("/instruments", dependencies=[Depends(require_gateway_secret)])
def instruments():
    content = _mstock_request("/openapi/typea/instruments/scriptmaster", raw=True)
    return PlainTextResponse(content.decode("utf-8-sig"), media_type="text/csv; charset=utf-8")


@app.get("/historical/{exchange}/{instrument_token}/{interval}", dependencies=[Depends(require_gateway_secret)])
def historical(
    exchange: str,
    instrument_token: str,
    interval: str,
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
):
    allowed_exchanges = {"NSE", "NFO", "BSE", "BFO"}
    allowed_intervals = {"minute", "day", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute"}
    cleaned_exchange = exchange.strip().upper()
    cleaned_interval = interval.strip().lower()
    if cleaned_exchange not in allowed_exchanges or not instrument_token.isdigit() or cleaned_interval not in allowed_intervals:
        raise HTTPException(status_code=400, detail="Invalid historical data request.")
    return _mstock_request(
        f"/openapi/typea/instruments/historical/{cleaned_exchange}/{instrument_token}/{cleaned_interval}",
        params={"from": from_date, "to": to_date},
    )


@app.post("/gainers-losers", dependencies=[Depends(require_gateway_secret)])
def gainers_losers(
    Exchange: int,
    SecurityIdCode: int,
    segment: int,
    TypeFlag: str,
):
    flag = TypeFlag.strip().upper()
    if flag not in {"G", "L"}:
        raise HTTPException(status_code=400, detail="TypeFlag must be G or L.")
    return _mstock_request(
        "/openapi/typea/losergainer",
        "POST",
        form={
            "Exchange": str(Exchange),
            "SecurityIdCode": str(SecurityIdCode),
            "segment": str(segment),
            "TypeFlag": flag,
        },
    )


@app.post("/order", dependencies=[Depends(require_gateway_secret)])
def place_order(payload: dict):
    side = str(payload.get("transaction_type") or payload.get("side") or "").strip().upper()
    symbol = str(payload.get("tradingsymbol") or payload.get("symbol") or "").strip().upper()
    exchange = str(payload.get("exchange") or "").strip().upper()
    product = str(payload.get("product") or "").strip().upper()
    order_type = str(payload.get("order_type") or "").strip().upper()
    validity = str(payload.get("validity") or "").strip().upper()
    quantity = payload.get("quantity")
    price = payload.get("price", "0")
    client_id = str(payload.get("client_id") or "").strip()

    if side not in {"BUY", "SELL"} or exchange not in {"NSE", "BSE"}:
        raise HTTPException(status_code=422, detail="Invalid order side or exchange.")
    if product not in {"CNC", "MIS"} or order_type not in {"MARKET", "LIMIT"} or validity not in {"DAY", "IOC"}:
        raise HTTPException(status_code=422, detail="Unsupported m.Stock order product, type, or validity.")
    if not isinstance(quantity, int) or quantity <= 0:
        raise HTTPException(status_code=422, detail="Order quantity must be a positive integer.")
    if not symbol:
        raise HTTPException(status_code=422, detail="Order trading symbol is required.")
    if exchange in {"NSE", "BSE"} and not symbol.endswith(("-EQ", "-BE", "-BZ", "-SM", "-ST", "-A", "-B", "-T")):
        symbol = f"{symbol}-EQ"
    try:
        numeric_price = float(price or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid order price.") from exc
    if order_type == "LIMIT" and numeric_price <= 0:
        raise HTTPException(status_code=422, detail="A positive limit price is required.")
    form = {
        "tradingsymbol": symbol,
        "exchange": exchange,
        "transaction_type": side,
        "order_type": order_type,
        "quantity": str(quantity),
        "product": product,
        "validity": validity,
        "price": str(numeric_price if order_type == "LIMIT" else 0),
    }
    if client_id:
        form["tag"] = hashlib.sha256(client_id.encode("utf-8")).hexdigest()[:20]

    result = _mstock_request(
        "/openapi/typea/orders/regular",
        "POST",
        form=form,
        allow_provider_error=True,
    )
    if result.get("status") not in {"success", True}:
        return {
            "success": False,
            "status": "rejected",
            "message": str(result.get("message") or "m.Stock rejected the order."),
            "data": result.get("data"),
        }
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    order_id = data.get("order_id") or data.get("orderid")
    if not order_id:
        return {
            "success": False,
            "status": "rejected",
            "message": "m.Stock did not confirm an order ID.",
            "data": data,
        }
    return {"success": True, "status": "success", "data": {"order_id": str(order_id)}}


@app.get("/orders", dependencies=[Depends(require_gateway_secret)])
def orders():
    return _mstock_request("/openapi/typea/orders")


@app.get("/tradebook", dependencies=[Depends(require_gateway_secret)])
def tradebook():
    return _mstock_request("/openapi/typea/tradebook")
