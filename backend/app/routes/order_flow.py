"""Authenticated, read-only Order Flow snapshot and WebSocket stream APIs."""
from __future__ import annotations

import asyncio
import re

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from fastapi import WebSocketDisconnect

from app.database.database import get_db
from app.routes.auth import get_current_user
from app.services.order_flow_feed import OrderFlowFeedError, get_order_flow_snapshot


router = APIRouter(prefix="/api/order-flow", tags=["Order Flow"])
# WebSockets authenticate with the existing Financial OS Bearer token supplied
# as a WebSocket subprotocol. This router is included separately so the normal
# HTTP-only router dependency does not reject the browser handshake.
stream_router = APIRouter(prefix="/api/order-flow", tags=["Order Flow Stream"])


def extract_bearer_token(protocol_header: str | None) -> str | None:
    """Read the Bearer token from the non-URL WebSocket subprotocol header."""
    for offered in (protocol_header or "").split(","):
        protocol = offered.strip()
        if protocol.startswith("bearer.") and len(protocol) > len("bearer."):
            return protocol[len("bearer."):]
    return None


def _authenticate_stream_token(token: str) -> bool:
    """Validate the same signed token and revocation record used by HTTP APIs."""
    db_dependency = get_db()
    db = next(db_dependency)
    try:
        get_current_user(
            authorization=f"Bearer {token}",
            credentials=None,
            db=db,
        )
        return True
    finally:
        db_dependency.close()


@router.get("/snapshot")
def order_flow_snapshot(
    symbol: str | None = Query(
        None, min_length=1, max_length=40,
        description="Optional underlying symbol, for example NIFTY",
    ),
    _current_user=Depends(get_current_user),
):
    cleaned = symbol.strip().upper() if symbol else None
    if cleaned and not re.fullmatch(r"(?=.*[A-Z0-9])[A-Z0-9&._-]{1,40}", cleaned):
        raise HTTPException(status_code=400, detail="Invalid underlying symbol.")
    try:
        return get_order_flow_snapshot(cleaned)
    except OrderFlowFeedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@stream_router.websocket("/stream")
async def order_flow_stream(websocket: WebSocket):
    token = extract_bearer_token(websocket.headers.get("sec-websocket-protocol"))
    if not token:
        await websocket.close(code=4401)
        return

    try:
        _authenticate_stream_token(token)
    except Exception:
        # Complete the handshake so browsers receive the explicit auth close
        # code and stop retrying with an expired/revoked Financial OS token.
        await websocket.accept(subprotocol="financial-os")
        await websocket.close(code=4401)
        return

    symbol = (websocket.query_params.get("symbol") or "").strip().upper()
    if symbol and not re.fullmatch(r"[A-Z0-9&._-]{1,40}", symbol):
        await websocket.close(code=4400)
        return

    await websocket.accept(subprotocol="financial-os")
    ensure_started = True

    try:
        while True:
            try:
                snapshot = await asyncio.to_thread(
                    get_order_flow_snapshot,
                    symbol or None,
                    ensure_started=ensure_started,
                )
                await websocket.send_json(snapshot)
                ensure_started = not bool((snapshot.get("stream") or {}).get("running"))
            except OrderFlowFeedError as exc:
                ensure_started = True
                await websocket.send_json({
                    "status": "error",
                    "message": str(exc),
                    "feed": {"status": "disconnected", "last_tick_at": None, "age_seconds": None},
                    "futures_contracts": [],
                    "option_contracts": [],
                    "option_oi_by_strike": [],
                })
            except WebSocketDisconnect:
                return
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
