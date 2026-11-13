"""Authenticated, read-only market order-flow analysis API.

The endpoint analyses provider-normalized market snapshots. It never places
orders, persists market data, or changes broker state.
"""
from fastapi import APIRouter, Body, HTTPException

from app.services.market_intelligence import (
    aggregate_sector_strength,
    calculate_option_metrics,
    classify_futures_position,
    score_conviction,
)

router = APIRouter(
    prefix="/api/market-order-flow",
    tags=["Market Order Flow"],
)


def analyze_market_order_flow(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="A market data object is required.")

    futures_rows = payload.get("futures", [])
    option_rows = payload.get("options", [])
    sector_rows = payload.get("sectors", [])

    if not any((futures_rows, option_rows, sector_rows)):
        raise HTTPException(
            status_code=422,
            detail="Provide at least one futures, options, or sectors dataset.",
        )

    if not all(isinstance(rows, list) for rows in (futures_rows, option_rows, sector_rows)):
        raise HTTPException(status_code=422, detail="Market datasets must be arrays.")

    futures = []
    for row in futures_rows:
        if not isinstance(row, dict):
            raise HTTPException(status_code=422, detail="Each futures row must be an object.")
        try:
            position = classify_futures_position(
                row.get("price_change_pct"),
                row.get("oi_change_pct"),
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Invalid futures price/OI change values.") from exc
        futures.append({
            "symbol": row.get("symbol"),
            "price_change_pct": row.get("price_change_pct"),
            "oi_change_pct": row.get("oi_change_pct"),
            "position": position,
        })

    options = None
    if option_rows:
        try:
            options = calculate_option_metrics(option_rows)
        except (TypeError, ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail=f"Invalid options dataset: {exc}") from exc

    sectors = []
    if sector_rows:
        try:
            sectors = aggregate_sector_strength(sector_rows)
        except (TypeError, ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail=f"Invalid sector dataset: {exc}") from exc

    conviction_input = payload.get("conviction")
    conviction = None
    if conviction_input is not None:
        if not isinstance(conviction_input, dict):
            raise HTTPException(status_code=422, detail="Conviction must be an object.")
        required_checks = (
            "positions_opened",
            "spot_agrees",
            "last_hour_agrees",
            "option_writers_agree",
            "sector_agrees",
        )
        if any(not isinstance(conviction_input.get(key), bool) for key in required_checks):
            raise HTTPException(status_code=422, detail="All five conviction checks must be boolean.")
        conviction = score_conviction(**{
            key: conviction_input[key] for key in required_checks
        })

    return {
        "status": "success",
        "engine": "Market Order Flow Intelligence",
        "version": "1.0",
        "read_only": True,
        "database_write": False,
        "futures": futures,
        "options": options,
        "sectors": sectors,
        "conviction": conviction,
    }


@router.post("/analyze")
def post_market_order_flow(payload: dict = Body(...)):
    """Analyse a normalized market snapshot; no trading or persistence side effects."""
    return analyze_market_order_flow(payload)
