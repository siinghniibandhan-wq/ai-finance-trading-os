"""Private Vercel service that adapts Financial OS gateway contracts to m.Stock Type-A APIs.

All routes are intended for internal service-to-service calls from the Financial OS API.
The shared gateway secret is checked on every request; broker orders remain protected
again by the Financial OS admin gate, persistent kill switch, and durable idempotency.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import os
import re
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
from pydantic import BaseModel

API_BASE_URL = os.getenv("MSTOCK_API_BASE_URL", "https://api.mstock.trade").rstrip("/")
API_KEY = os.getenv("MSTOCK_API_KEY", "").strip()
GATEWAY_SECRET = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
TOTP_SECRET = os.getenv("MSTOCK_TOTP_SECRET", "").strip()
STATIC_ACCESS_TOKEN = os.getenv("MSTOCK_ACCESS_TOKEN", "").strip()
REQUEST_TIMEOUT_SECONDS = 15
SESSION_REQUIRED_PREFIX = "MSTOCK_SESSION_REQUIRED"
logger = logging.getLogger("mstock_gateway")

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


# ---------------------------------------------------------------------------
# Shared session storage
# A serverless instance can restart or run in parallel, so the access token is
# also kept (encrypted) in the existing Postgres database. The 6-digit TOTP is
# used once to obtain the token; it is never stored.
# ---------------------------------------------------------------------------

def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    for prefix in ("postgresql+psycopg://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql://" + url[len(prefix):]
    return url


def _fernet():
    from cryptography.fernet import Fernet

    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    key = base64.urlsafe_b64encode(hashlib.sha256(f"mstock-session:{secret}".encode("utf-8")).digest())
    return Fernet(key)


def _db_connect():
    import psycopg

    url = _database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured.")
    conn = psycopg.connect(url, connect_timeout=5, autocommit=True)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS mstock_gateway_session ("
        "id SMALLINT PRIMARY KEY, token_encrypted TEXT NOT NULL, "
        "expires_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    return conn


def _store_session(token: str, expires_at: datetime) -> bool:
    """Persist the token for all instances. Returns False when the database is unavailable."""
    try:
        encrypted = _fernet().encrypt(token.encode("utf-8")).decode("utf-8")
        with _db_connect() as conn:
            conn.execute(
                "INSERT INTO mstock_gateway_session (id, token_encrypted, expires_at, updated_at) "
                "VALUES (1, %s, %s, now()) ON CONFLICT (id) DO UPDATE SET "
                "token_encrypted = EXCLUDED.token_encrypted, expires_at = EXCLUDED.expires_at, updated_at = now()",
                (encrypted, expires_at),
            )
        return True
    except Exception as exc:  # noqa: BLE001 - never leak details or break market data
        logger.warning("Could not persist m.Stock session: %s", type(exc).__name__)
        return False


def _load_session() -> tuple[str, datetime] | None:
    try:
        with _db_connect() as conn:
            row = conn.execute(
                "SELECT token_encrypted, expires_at FROM mstock_gateway_session WHERE id = 1"
            ).fetchone()
        if not row:
            return None
        token = _fernet().decrypt(row[0].encode("utf-8")).decode("utf-8")
        expires_at = row[1]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        return token, expires_at
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load m.Stock session: %s", type(exc).__name__)
        return None


def _clear_session() -> None:
    global _cached_access_token, _cached_token_expires_at
    _cached_access_token = None
    _cached_token_expires_at = None
    try:
        with _db_connect() as conn:
            conn.execute("DELETE FROM mstock_gateway_session WHERE id = 1")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not clear m.Stock session: %s", type(exc).__name__)


def _normalised_totp_secret() -> str | None:
    """Return the TOTP seed only if it is a valid Base32 key; never raises."""
    candidate = re.sub(r"[\s-]", "", TOTP_SECRET or "").upper()
    if not candidate:
        return None
    try:
        base64.b32decode(candidate + "=" * (-len(candidate) % 8), casefold=True)
    except (binascii.Error, ValueError):
        return None
    return candidate




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


def _login_with_totp(seed: str | None = None) -> str:
    if not API_KEY:
        raise HTTPException(status_code=503, detail="MSTOCK_API_KEY is not configured.")
    seed = seed or TOTP_SECRET
    if not seed:
        raise HTTPException(
            status_code=503,
            detail="MSTOCK_TOTP_SECRET is not configured; enable m.Stock Trading API TOTP.",
        )

    payload = _post_totp_session(_generate_fresh_totp(seed))
    if _is_totp_rejection(payload):
        # A rejected code may have crossed a 30-second boundary in transit.
        # Wait for the next period and make exactly one fresh attempt.
        payload = _post_totp_session(_generate_fresh_totp(seed, next_period=True))

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


def _token_valid(token: str | None, expires_at: datetime | None) -> bool:
    return bool(token and expires_at and _now_ist() < expires_at)


def _session_required() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"{SESSION_REQUIRED_PREFIX}: Enter your current m.Stock TOTP code to connect.",
    )


def _get_access_token(force_refresh: bool = False) -> str:
    global _cached_access_token, _cached_token_expires_at

    if STATIC_ACCESS_TOKEN:
        if not API_KEY:
            raise HTTPException(status_code=503, detail="MSTOCK_API_KEY is not configured.")
        return STATIC_ACCESS_TOKEN

    if not force_refresh and _token_valid(_cached_access_token, _cached_token_expires_at):
        return _cached_access_token

    with _token_lock:
        rejected = _cached_access_token if force_refresh else None
        if not force_refresh and _token_valid(_cached_access_token, _cached_token_expires_at):
            return _cached_access_token

        # Another instance may already hold a newer valid session.
        stored = _load_session()
        if stored and _token_valid(*stored) and stored[0] != rejected:
            _cached_access_token, _cached_token_expires_at = stored
            return _cached_access_token

        if force_refresh:
            _clear_session()

        # Optional automatic login, only when a valid Base32 seed is configured.
        seed = _normalised_totp_secret()
        if seed and API_KEY:
            try:
                token = _login_with_totp(seed)
                _cached_access_token = token
                _cached_token_expires_at = _local_token_expiry()
                _store_session(token, _cached_token_expires_at)
                return token
            except HTTPException as exc:
                logger.warning("Automatic TOTP login failed (HTTP %s).", exc.status_code)

        raise _session_required()


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
        "authentication": "static-token" if STATIC_ACCESS_TOKEN else ("totp-seed" if _normalised_totp_secret() else "typed-totp-session"),
    }


class SessionRequest(BaseModel):
    totp: str


@app.get("/session", dependencies=[Depends(require_gateway_secret)])
def session_status():
    """Report whether a usable m.Stock session exists. Never returns the token."""
    if STATIC_ACCESS_TOKEN:
        return {"connected": True, "mode": "static-token", "expires_at": None}
    if _token_valid(_cached_access_token, _cached_token_expires_at):
        return {"connected": True, "mode": "session", "expires_at": _cached_token_expires_at.isoformat()}
    stored = _load_session()
    if stored and _token_valid(*stored):
        return {"connected": True, "mode": "session", "expires_at": stored[1].isoformat()}
    return {"connected": False, "mode": "totp-required", "expires_at": None}


@app.post("/session", dependencies=[Depends(require_gateway_secret)])
def create_session(body: SessionRequest):
    """Exchange one typed 6-digit TOTP for an m.Stock access token and keep it until it expires."""
    global _cached_access_token, _cached_token_expires_at

    code = body.totp.strip()
    if not re.fullmatch(r"\d{6}", code):
        raise HTTPException(status_code=400, detail="Enter the 6-digit code from your authenticator app.")
    if not API_KEY:
        raise HTTPException(status_code=503, detail="MSTOCK_API_KEY is not configured.")

    payload = _post_totp_session(code)
    if payload.get("status") not in {"success", True}:
        if str(payload.get("error_type") or "").lower() == "apikeyexception":
            raise HTTPException(
                status_code=503,
                detail="m.Stock API key is invalid, expired, or suspended. Check the broker API subscription.",
            )
        raise HTTPException(
            status_code=400,
            detail="m.Stock did not accept that code. Wait for the next code and try again.",
        )
    data = payload.get("data")
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token.strip():
        raise HTTPException(status_code=502, detail="m.Stock did not return an access token.")

    token = token.strip()
    expires_at = _local_token_expiry()
    with _token_lock:
        _cached_access_token = token
        _cached_token_expires_at = expires_at
    persisted = _store_session(token, expires_at)
    return {"connected": True, "expires_at": expires_at.isoformat(), "shared_across_instances": persisted}


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
