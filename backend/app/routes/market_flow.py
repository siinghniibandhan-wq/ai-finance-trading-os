"""Read-only Chart Flow adapter over the existing working Market Overview feed.

Markets and Advanced Chart remain the source of truth for market-data access.
Chart Flow deliberately reuses the same Market Overview provider path so it
cannot drift into a second, independently configured broker integration.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.routes.market_overview import get_market_overview

router = APIRouter(prefix="/api/market-flow", tags=["Market Flow"])


@router.get("/")
def get_market_flow_snapshot():
    """Adapt the established Market Overview response for the Chart Flow UI."""
    try:
        overview = get_market_overview()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"message": "Unable to retrieve Chart Flow market data.", "reason": str(exc)},
        ) from exc

    if not isinstance(overview, dict):
        raise HTTPException(status_code=502, detail="Market Overview returned an invalid response.")

    movers = overview.get("market_movers") or {}
    gainers = movers.get("gainers") if isinstance(movers, dict) else []
    losers = movers.get("losers") if isinstance(movers, dict) else []
    gainers = [row for row in gainers if isinstance(row, dict)]
    losers = [row for row in losers if isinstance(row, dict)]
    indices = overview.get("indices") if isinstance(overview.get("indices"), list) else []
    indices = [row for row in indices if isinstance(row, dict)]
    errors = overview.get("errors") if isinstance(overview.get("errors"), list) else []

    if overview.get("status") == "error" and not indices and not gainers and not losers:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve Chart Flow market data.",
                "errors": errors,
            },
        )

    status = "partial" if overview.get("status") == "partial" or errors else "success"
    timestamp = overview.get("last_updated") or datetime.now(timezone.utc).isoformat()

    return {
        "status": status,
        "engine": "Chart Flow Market Snapshot",
        "version": "1.1",
        "read_only": True,
        "scope": {
            "source": "existing Market Overview Engine",
            "exchanges": sorted({
                str(row.get("exchange")).upper()
                for row in gainers + losers
                if row.get("exchange")
            }),
            "universe": "Provider-returned Market Overview top gainers and losers",
            "note": "This is the same mover set used by Markets, not full-exchange breadth.",
        },
        "indices": indices,
        "market_movers": {"gainers": gainers, "losers": losers},
        "market_summary": {
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": None,
            "total_returned": len(gainers) + len(losers),
        },
        "capabilities": {
            "working_market_overview_feed": True,
            "full_advance_decline_breadth": False,
            "sector_classification": any(row.get("sector") for row in gainers + losers),
            "delivery_statistics": False,
            "historical_market_flow": False,
        },
        "limitations": [
            "The provider mover feed contains top gainers and losers, not every unchanged listing.",
            "Sector participation is shown only when the provider supplies sector classification.",
            "The Market Overview retrieval timestamp is not an exchange event timestamp.",
        ],
        "data_sources": overview.get("data_sources") or {
            "primary": "Existing Market Overview Engine",
        },
        "last_updated": timestamp,
        "errors": errors,
        "database_write": False,
    }
