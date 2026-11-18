"""
Financial OS — Market Overview Engine v1.2

Purpose:
- Combine existing market indices and market movers.
- Reuse existing provider functions and m.Stock gateway.
- Return partial results when one data source fails.
- Read-only: no database writes.
"""

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    # Run independent Type A provider requests concurrently. A slow index or
    # movers response must not hold up every other market card in the overview.
    index_results = {}
    mover_results = {"gainers": [], "losers": []}
    errors = []

    jobs = {}
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="market-overview") as executor:
        for index in SUPPORTED_INDICES:
            future = executor.submit(fetch_index, index)
            jobs[future] = ("index", index)

        for mover_type in ("gainers", "losers"):
            future = executor.submit(fetch_overview_movers, mover_type)
            jobs[future] = ("movers", mover_type)

        for future in as_completed(jobs):
            source_type, source = jobs[future]
            try:
                result = future.result()
                if source_type == "index":
                    index_results[source["name"]] = result
                else:
                    mover_results[source] = result
            except Exception as exc:
                if source_type == "index":
                    errors.append({
                        "source": "market_indices",
                        "name": source["name"],
                        "message": str(exc),
                    })
                else:
                    errors.append({
                        "source": "market_movers",
                        "type": source,
                        "message": str(exc),
                    })

    # Preserve the configured benchmark order regardless of completion order.
    indices = [
        index_results[index["name"]]
        for index in SUPPORTED_INDICES
        if index["name"] in index_results
    ]
    gainers = mover_results["gainers"]
    losers = mover_results["losers"]
    errors.sort(key=lambda item: (item.get("source", ""), item.get("name", item.get("type", ""))))

    if errors and not indices and not gainers and not losers:
        response_status = "error"
    elif errors:
        response_status = "partial"
    else:
        response_status = "success"

    return {
        "status": response_status,
        "engine": "Market Overview Engine",
        "version": "1.3",
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
            "primary": "m.Stock via m.Stock Gateway",
            "indices": "Market Indices Engine",
            "market_movers": "Market Movers Engine",
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
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
