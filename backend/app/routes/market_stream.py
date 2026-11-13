"""Authenticated read-only status and snapshot for the optional m.Stock market stream."""
from fastapi import APIRouter

from app.services.mstock_stream_runtime import market_stream_runtime

router = APIRouter(prefix="/api/market-stream", tags=["Market Stream"])


@router.get("/status")
def get_market_stream_status():
    return market_stream_runtime.status()


@router.get("/snapshot")
def get_market_stream_snapshot():
    return market_stream_runtime.snapshot()
