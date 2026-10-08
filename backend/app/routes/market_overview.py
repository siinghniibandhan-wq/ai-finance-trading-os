"""
Financial OS — Market Overview Engine v1.0

Purpose:
- Provide a clean market-workspace summary.
- Keep market workspace logic separate from market.py.
- Use the existing market provider layer where possible.
- Read-only.
- No database writes.

IMPORTANT:
- Existing market.py is NOT modified.
- Existing AWS → m.Stock integration remains unchanged.
"""

from datetime import datetime, timezone
from fastapi import APIRouter


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
    """
    Return the initial Market Workspace overview.

    This v1 endpoint establishes the workspace structure.
    Provider-specific index/mover/history integrations will
    be added through separate modules.

    No database changes are performed.
    """

    return {
        "status": "success",
        "engine": "Market Overview Engine",
        "version": "1.0",
        "read_only": True,

        "market_status": {
            "status": "unknown",
            "source": "not_connected_yet",
        },

        "indices": [],

        "market_summary": {
            "gainers": 0,
            "losers": 0,
            "unchanged": 0,
        },

        "data_sources": {
            "primary": "m.Stock via AWS Gateway",
            "market_price_service": "market.py",
        },

        "last_updated": datetime.now(
            timezone.utc
        ).isoformat(),

        "modules": {
            "overview": True,
            "quote": False,
            "search": False,
            "historical_data": False,
            "charts": False,
            "watchlist": False,
            "market_movers": False,
        },

        "database_write": False,

        "next_module": "Market Quote Engine",
    }
