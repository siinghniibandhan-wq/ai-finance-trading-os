"""Authenticated, read-only Order Flow derivatives snapshot API."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.order_flow_feed import OrderFlowFeedError, get_order_flow_snapshot
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/order-flow", tags=["Order Flow"])


@router.get("/snapshot")
def order_flow_snapshot(
    symbol: str | None = Query(
        None, min_length=1, max_length=40,
        description="Optional underlying symbol, for example NIFTY",
    ),
    _current_user=Depends(get_current_user),
):
    """Return the latest normalized futures and option OI snapshot."""
    cleaned = symbol.strip().upper() if symbol else None
    if cleaned and not cleaned.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid underlying symbol.")
    try:
        return get_order_flow_snapshot(cleaned)
    except OrderFlowFeedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
