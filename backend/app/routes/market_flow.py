"""Provider-backed, read-only cash-equity market-flow snapshot for Chart Flow."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.routes.market_indices import SUPPORTED_INDICES, fetch_index
from app.routes.market_movers import (
    extract_type_a_mover_rows,
    fetch_movers,
    normalize_mover,
)

router = APIRouter(prefix="/api/market-flow", tags=["Market Flow"])

# m.Stock Type A documentation: SecurityIdCode=0 means ALL.
# Exchange/segment pairs are 1/1 for NSE and 4/2 for BSE.
CASH_EXCHANGES = (
    {"name": "NSE", "exchange": 1, "segment": 1},
    {"name": "BSE", "exchange": 4, "segment": 2},
)


def fetch_all_cash_movers():
    """Fetch the provider's ALL-universe gainer and loser lists for both exchanges."""
    movers = {"gainers": [], "losers": []}
    errors = []
    seen = {"gainers": set(), "losers": set()}
    request_count = 0

    for exchange in CASH_EXCHANGES:
        for mover_type, type_flag in (("gainers", "G"), ("losers", "L")):
            # m.Stock documents a 1-request/second data-API limit.
            if request_count:
                time.sleep(1.05)
            request_count += 1
            try:
                response = fetch_movers(
                    exchange=exchange["exchange"],
                    security_id_code=0,
                    segment=exchange["segment"],
                    type_flag=type_flag,
                )
                rows = extract_type_a_mover_rows(response)
                for raw in rows:
                    if not isinstance(raw, dict):
                        continue
                    item = normalize_mover(raw)
                    item_exchange = str(item.get("exchange") or exchange["name"]).upper()
                    symbol = str(item.get("symbol") or "").strip().upper()
                    if item_exchange not in {"NSE", "BSE"} or not symbol:
                        continue
                    item["exchange"] = item_exchange
                    key = item_exchange + ":" + symbol
                    if key in seen[mover_type]:
                        continue
                    seen[mover_type].add(key)
                    movers[mover_type].append(item)
            except Exception as exc:
                errors.append({
                    "source": "m.Stock",
                    "exchange": exchange["name"],
                    "type": mover_type,
                    "message": str(exc),
                })

    return movers, errors


@router.get("/")
def get_market_flow_snapshot():
    movers, errors = fetch_all_cash_movers()

    indices = []
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="market-flow-index") as executor:
        jobs = {executor.submit(fetch_index, index): index for index in SUPPORTED_INDICES}
        for future in as_completed(jobs):
            index = jobs[future]
            try:
                indices.append(future.result())
            except Exception as exc:
                errors.append({
                    "source": "market_indices",
                    "name": index["name"],
                    "message": str(exc),
                })

    indices.sort(key=lambda item: next(
        (position for position, configured in enumerate(SUPPORTED_INDICES)
         if configured["name"] == item.get("name")),
        len(SUPPORTED_INDICES),
    ))

    gainers = movers["gainers"]
    losers = movers["losers"]
    if errors and not indices and not gainers and not losers:
        raise HTTPException(
            status_code=502,
            detail={"message": "Unable to retrieve Chart Flow market data.", "errors": errors},
        )

    return {
        "status": "partial" if errors else "success",
        "engine": "Chart Flow Market Snapshot",
        "version": "1.0",
        "read_only": True,
        "scope": {
            "exchanges": ["NSE", "BSE"],
            "universe": "ALL cash-market instruments supported by m.Stock's gainer/loser endpoint",
            "security_id_code": 0,
            "note": "The provider returns top gainers and losers, not every unchanged listing.",
        },
        "indices": indices,
        "market_movers": movers,
        "market_summary": {
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": None,
            "total_returned": len(gainers) + len(losers),
        },
        "capabilities": {
            "all_exchange_mover_lists": True,
            "full_advance_decline_breadth": False,
            "sector_classification": False,
            "delivery_statistics": False,
            "historical_market_flow": False,
        },
        "limitations": [
            "Top gainer/loser lists do not include unchanged stocks, so they cannot establish full-market breadth.",
            "The current provider mover response does not include sector classification or delivery statistics.",
            "The index route exposes gateway retrieval time, not an exchange timestamp.",
        ],
        "data_sources": {
            "primary": "m.Stock via Financial OS Gateway",
            "movers": "m.Stock Type A Top Gainers and Losers API, SecurityIdCode=0 (ALL)",
            "indices": "Existing Financial OS Market Indices Engine",
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "errors": errors,
        "database_write": False,
    }
