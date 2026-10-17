"""Owner-only live-trading control for the local m.Stock gateway.

This router never submits an order. It only reads gateway status and changes the
gateway's process-local trading-enabled flag.
"""
import json
import logging
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models import User
from app.routes.auth import get_current_admin

router = APIRouter(prefix="/api/broker", tags=["Broker Trading Control"])
logger = logging.getLogger(__name__)
_TIMEOUT_SECONDS = 5


class TradingToggleRequest(BaseModel):
    enabled: bool


def _gateway_base_url() -> str:
    # This control is intentionally restricted to the same host. Do not send a
    # gateway secret to a public IP or over non-loopback plaintext HTTP.
    value = os.getenv("MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000").rstrip("/")
    if value not in {"http://127.0.0.1:8000", "http://localhost:8000"}:
        raise HTTPException(
            status_code=503,
            detail="Trading control requires the m.Stock gateway on loopback HTTP.",
        )
    return value


def _gateway_request(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    base = _gateway_base_url()
    headers = {"Accept": "application/json", "User-Agent": "Financial-OS/1.0"}
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if path == "/trading-toggle":
        if not secret:
            raise HTTPException(
                status_code=503,
                detail="MSTOCK_GATEWAY_SECRET must be configured before trading can be toggled.",
            )
        headers["X-Financial-OS-Gateway-Secret"] = secret
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{base}{path}", data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            if response.status >= 400 or not isinstance(data, dict):
                raise HTTPException(status_code=502, detail="Invalid response from m.Stock gateway.")
            return data
    except HTTPError as exc:
        # Never expose the gateway response body, which might contain internals.
        raise HTTPException(status_code=502, detail=f"m.Stock gateway returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Trading-control gateway request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Unable to verify m.Stock gateway trading status.") from exc


@router.get("/trading-owner")
def get_trading_owner(admin: User = Depends(get_current_admin)):
    """Return owner visibility only to the configured platform administrator."""
    return {"is_owner": True}


@router.get("/trading-status")
def get_trading_status(admin: User = Depends(get_current_admin)):
    status = _gateway_request("/trading-status")
    if not isinstance(status.get("trading_enabled"), bool):
        raise HTTPException(status_code=502, detail="Gateway trading status is missing or invalid.")
    # Limits are read-only and are returned exactly as reported by the gateway.
    return {
        "trading_enabled": status["trading_enabled"],
        "max_order_value": status.get("max_order_value"),
        "max_order_qty": status.get("max_order_qty"),
    }


@router.post("/trading-toggle")
def set_trading_status(
    request: TradingToggleRequest,
    admin: User = Depends(get_current_admin),
):
    result = _gateway_request("/trading-toggle", method="POST", payload={"enabled": request.enabled})
    if result.get("trading_enabled") is not request.enabled:
        raise HTTPException(status_code=502, detail="Gateway did not confirm the requested trading state.")
    timestamp = datetime.now(timezone.utc).isoformat()
    # Do not log tokens, gateway secrets, TOTP codes, or request bodies.
    logger.warning(
        "LIVE_TRADING_STATE_CHANGED actor_user_id=%s enabled=%s timestamp_utc=%s",
        admin.id,
        request.enabled,
        timestamp,
    )
    return {
        "trading_enabled": request.enabled,
        "changed_at": timestamp,
        "max_order_value": result.get("max_order_value"),
        "max_order_qty": result.get("max_order_qty"),
    }
