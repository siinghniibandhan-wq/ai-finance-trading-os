"""Authenticated m.Stock broker-session controls shared by Markets and Order Flow."""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.routes.auth import get_current_user
from app.services.order_flow_feed import (
    OrderFlowFeedError,
    get_order_flow_snapshot,
)


router = APIRouter(prefix="/api/market-broker", tags=["Market Broker"])


class MStockAuthenticationRequest(BaseModel):
    totp: str = Field(pattern=r"^[0-9]{6}$")


class MarketBrokerError(Exception):
    """Raised when the authenticated m.Stock gateway cannot be reached."""


def _gateway_config() -> tuple[str, str]:
    base = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if not base or not secret:
        raise MarketBrokerError("m.Stock gateway URL or shared-secret authentication is not configured.")
    return base, secret


def _gateway_request(path: str, *, method: str = "GET", form: dict | None = None) -> dict:
    base, secret = _gateway_config()
    data = urlencode(form).encode("utf-8") if form is not None else None
    headers = {
        "Accept": "application/json",
        "X-Financial-OS-Gateway-Secret": secret,
        "User-Agent": "Financial-OS/1.0",
    }
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not forward raw provider bodies; they may contain session details.
        if exc.code == 401:
            raise MarketBrokerError("m.Stock rejected the OTP or the broker session.") from exc
        if exc.code == 403:
            raise MarketBrokerError("The m.Stock gateway rejected Financial OS authentication.") from exc
        raise MarketBrokerError(f"m.Stock gateway returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise MarketBrokerError("Unable to connect to the m.Stock gateway.") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise MarketBrokerError("m.Stock gateway returned an invalid response.") from exc
    if not isinstance(payload, dict):
        raise MarketBrokerError("m.Stock gateway returned an invalid response.")
    return payload


def authenticate_broker_session(totp: str) -> dict:
    """Authenticate once at the gateway; the gateway shares its token with REST and WebSocket."""
    code = str(totp or "").strip()
    if not re.fullmatch(r"[0-9]{6}", code):
        raise MarketBrokerError("Enter the current six-digit m.Stock TOTP.")
    payload = _gateway_request("/auth", method="POST", form={"totp": code})
    if payload.get("status") != "success":
        raise MarketBrokerError(str(payload.get("message") or "m.Stock authentication failed.")[:200])

    # Start the existing F&O worker after authentication. A transport failure
    # must not turn a valid OTP into a failed broker login; report it separately.
    try:
        snapshot = get_order_flow_snapshot()
        feed = snapshot.get("feed") if isinstance(snapshot, dict) else None
        stream = snapshot.get("stream") if isinstance(snapshot, dict) else None
        market_stream = {
            "status": str((feed or {}).get("status") or "disconnected"),
            "connected": bool((stream or {}).get("connected")),
            "last_tick_at": (feed or {}).get("last_tick_at"),
            "message": None,
        }
    except OrderFlowFeedError as exc:
        market_stream = {
            "status": "unavailable",
            "connected": False,
            "last_tick_at": None,
            "message": str(exc),
        }

    return {
        "status": "success",
        "broker": "m.Stock",
        "broker_authenticated": True,
        "message": "m.Stock session authenticated. The same gateway session is used by Market REST and Market Flow WebSocket.",
        "market_stream": market_stream,
    }


def get_broker_session_status() -> dict:
    payload = _gateway_request("/auth/status")
    if payload.get("status") != "success":
        raise MarketBrokerError(str(payload.get("message") or "Unable to read m.Stock session status.")[:200])
    return {
        "status": "success",
        "broker": "m.Stock",
        "authenticated": bool(payload.get("authenticated")),
        "expires_in_seconds": payload.get("expires_in_seconds"),
        "stream": payload.get("stream") if isinstance(payload.get("stream"), dict) else {},
    }


@router.get("/status")
def broker_session_status(_current_user=Depends(get_current_user)):
    try:
        return get_broker_session_status()
    except MarketBrokerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/authenticate")
def broker_session_authenticate(
    request: MStockAuthenticationRequest,
    _current_user=Depends(get_current_user),
):
    try:
        return authenticate_broker_session(request.totp)
    except MarketBrokerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
