"""
Financial OS — Market Overview Engine v1.2

Purpose:
- Combine existing market indices and market movers.
- Reuse existing provider functions and m.Stock gateway.
- Return partial results when one data source fails.
- Read-only: no database writes.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.routes.market_indices import (
    SUPPORTED_INDICES,
    fetch_index,
)

from app.routes.market_movers import fetch_movers


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/market-overview",
    tags=["Market Overview"],
)


# ============================================================
# MARKET MOVERS CONFIGURATION
# Reuses the existing Market Movers provider function.
# ============================================================

DEFAULT_EXCHANGE = 1
DEFAULT_SECURITY_ID_CODE = 13
DEFAULT_SEGMENT = 1
DEFAULT_MOVER_LIMIT = 20


# ============================================================
# FETCH AND NORMALIZE MARKET MOVERS
# Does not call the FastAPI route directly.
# Does not make an HTTP request to this application.
# ============================================================

def fetch_overview_movers(mover_type: str):
    """
    Fetch gainers or losers using the existing provider function.

    mover_type:
        gainers -> G
        losers  -> L
    """

    # --------------------------------------------------------
    # Validate the requested mover type
    # --------------------------------------------------------

    mover_type = mover_type.strip().lower()

    if mover_type not in ("gainers", "losers"):
        raise ValueError(
            "Mover type must be gainers or losers"
        )

    type_flag = (
        "G" if mover_type == "gainers" else "L"
    )

    # --------------------------------------------------------
    # Request data from the existing m.Stock gateway integration
    # --------------------------------------------------------

    provider_response = fetch_movers(
        exchange=DEFAULT_EXCHANGE,
        security_id_code=DEFAULT_SECURITY_ID_CODE,
        segment=DEFAULT_SEGMENT,
        type_flag=type_flag,
    )

    # --------------------------------------------------------
    # Validate provider response
    # --------------------------------------------------------

    if not isinstance(provider_response, dict):
        raise ValueError(
            "Invalid Market Movers provider response"
        )

    if not provider_response.get("status"):
        raise ValueError(
            "Market Movers provider request failed"
        )

    raw_data = provider_response.get("data", [])

    if not isinstance(raw_data, list):
        raise ValueError(
            "Market Movers provider returned invalid data"
        )

    # --------------------------------------------------------
    # Normalize the existing provider data
    # Keep the same response fields as Market Movers Engine
    # --------------------------------------------------------

    movers = []

    for item in raw_data[:DEFAULT_MOVER_LIMIT]:

        if not isinstance(item, dict):
            continue

        movers.append({
            "symbol": item.get("symbol"),

            "name": (
                item.get("symbol_name")
                or item.get("display_name")
            ),

            "exchange": item.get("exchange"),
            "segment": item.get("segment"),
            "security_id": item.get("security_id"),
            "ltp": item.get("ltp"),
            "change": item.get("change"),

            "percent_change": item.get("per_change"),

            "volume": item.get("volume"),
            "instrument": item.get("instrument"),
            "series": item.get("series"),
            "isin": item.get("isin"),
        })

    return movers


# ============================================================
# MARKET OVERVIEW ENDPOINT
# ============================================================

@router.get("/")
def get_market_overview():

    indices = []
    gainers = []
    losers = []
    errors = []

    # --------------------------------------------------------
    # 1. FETCH MARKET INDICES
    # NIFTY 50 and SENSEX are fetched independently.
    # --------------------------------------------------------

    for index in SUPPORTED_INDICES:

        try:
            index_data = fetch_index(index)
            indices.append(index_data)

        except Exception as exc:
            errors.append({
                "source": "market_indices",
                "name": index["name"],
                "message": str(exc),
            })

    # --------------------------------------------------------
    # 2. FETCH GAINERS AND LOSERS
    # Uses the existing provider function directly.
    # --------------------------------------------------------

    for mover_type, target in (
        ("gainers", gainers),
        ("losers", losers),
    ):

        try:
            mover_data = fetch_overview_movers(
                mover_type
            )

            target.extend(mover_data)

        except Exception as exc:
            errors.append({
                "source": "market_movers",
                "type": mover_type,
                "message": str(exc),
            })

    # --------------------------------------------------------
    # 3. DETERMINE OVERALL RESPONSE STATUS
    # --------------------------------------------------------

    if errors and not indices and not gainers and not losers:

        response_status = "error"

    elif errors:

        response_status = "partial"

    else:

        response_status = "success"

    # --------------------------------------------------------
    # 4. RETURN CONSOLIDATED MARKET OVERVIEW
    # --------------------------------------------------------

    return {
        "status": response_status,

        "engine": "Market Overview Engine",
        "version": "1.2",

        "read_only": True,

        # ----------------------------------------------------
        # Market status
        # ----------------------------------------------------

        "market_status": {
            "status": "unknown",
            "source": "not_connected",
        },

        # ----------------------------------------------------
        # Market indices
        # ----------------------------------------------------

        "indices": indices,

        # ----------------------------------------------------
        # Market summary
        # ----------------------------------------------------

        "market_summary": {
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": 0,
        },

        # ----------------------------------------------------
        # Gainers and losers
        # ----------------------------------------------------

        "market_movers": {
            "gainers": gainers,
            "losers": losers,
        },

        # ----------------------------------------------------
        # Data source information
        # ----------------------------------------------------

        "data_sources": {
            "primary": "m.Stock via m.Stock Gateway",
            "indices": "Market Indices Engine",
            "market_movers": "Market Movers Engine",
        },

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        "last_updated": datetime.now(
            timezone.utc
        ).isoformat(),

        # ----------------------------------------------------
        # Registered backend module indicators
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Errors, if any
        # ----------------------------------------------------

        "errors": errors,

        "database_write": False,

        "next_module": "Market Workspace Integration",
    }
