"""
Financial OS — Market Overview Engine v1.1

Purpose:
- Connect market indices and market movers.
- Reuse existing market modules and AWS gateway.
- Return partial results if one data source fails.
- Read-only; no database writes.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.routes.market_indices import (
    SUPPORTED_INDICES,
    fetch_index,
)
from app.routes.market_movers import get_market_movers


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/market-overview",
    tags=["Market Overview"],
)


# ============================================================
# MARKET OVERVIEW
# ============================================================

@router.get("/")
def get_market_overview():
    indices = []
    gainers = []
    losers = []
    errors = []

    # --------------------------------------------------------
    # Fetch NIFTY 50 and SENSEX independently
    # --------------------------------------------------------

    for index in SUPPORTED_INDICES:
        try:
            indices.append(fetch_index(index))
        except Exception as exc:
            errors.append({
                "source": "market_indices",
                "name": index["name"],
                "message": str(exc),
            })

    # --------------------------------------------------------
    # Fetch gainers and losers independently
    # --------------------------------------------------------

    for mover_type, target in (
        ("gainers", gainers),
        ("losers", losers),
    ):
        try:
            result = get_market_movers(type=mover_type)
            target.extend(result.get("movers", []))
        except Exception as exc:
            errors.append({
                "source": "market_movers",
                "type": mover_type,
                "message": str(exc),
            })

    # --------------------------------------------------------
    # Determine response status
    # --------------------------------------------------------

    if errors and not indices and not gainers and not losers:
        response_status = "error"
    elif errors:
        response_status = "partial"
    else:
        response_status = "success"

    # --------------------------------------------------------
    # Return consolidated overview
    # --------------------------------------------------------

    return {
        "status": response_status,
        "engine": "Market Overview Engine",
        "version": "1.1",
        "read_only": True,

        "market_status": {
            "status": "unknown",
            "source": "not_connected",
        },

        "indices": indices,

        "market_summary": {
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": 0,
        },

        "market_movers": {
            "gainers": gainers,
            "losers": losers,
        },

        "data_sources": {
            "primary": "m.Stock via AWS Gateway",
            "indices": "Market Indices Engine",
            "market_movers": "Market Movers Engine",
        },

        "last_updated": datetime.now(
            timezone.utc
        ).isoformat(),

        "modules": {
            "overview": True,
            "quote": True,
            "search": True,
            "historical_data": True,
            "charts": True,
            "watchlist": True,
            "market_movers": True,
            "market_indices": True,
        },

        "errors": errors,
        "database_write": False,
        "next_module": "Market Workspace Integration",
    }
