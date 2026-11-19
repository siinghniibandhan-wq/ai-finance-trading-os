"""Provider-backed, read-only cash-equity market-flow snapshot for Chart Flow."""

import time
import threading
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


# One shared limiter for Chart Flow mover requests. m.Stock documents one
# data-API request per second; it must also cover concurrent market/sector calls.
_mstock_mover_lock = threading.Lock()
_last_mstock_mover_request_at = 0.0
MSTOCK_MOVER_MIN_INTERVAL_SECONDS = 1.05


def _fetch_mstock_movers(**kwargs):
    global _last_mstock_mover_request_at
    with _mstock_mover_lock:
        now = time.monotonic()
        wait = MSTOCK_MOVER_MIN_INTERVAL_SECONDS - (now - _last_mstock_mover_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_mstock_mover_request_at = time.monotonic()
        return fetch_movers(**kwargs)


def fetch_all_cash_movers():
    """Fetch the provider's ALL-universe gainer and loser lists for both exchanges."""
    movers = {"gainers": [], "losers": []}
    errors = []
    seen = {"gainers": set(), "losers": set()}
    for exchange in CASH_EXCHANGES:
        for mover_type, type_flag in (("gainers", "G"), ("losers", "L")):
            try:
                response = _fetch_mstock_movers(
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


# Provider-documented NSE sector universes for the Type A Top Gainers/Losers API.
# These codes are SecurityIdCode values, not invented sector classifications.
SECTOR_UNIVERSES = (
    {"key": "auto", "name": "Automobile", "security_id_code": 9, "index_symbol": "NIFTY AUTO"},
    {"key": "private-bank", "name": "Private Banks", "security_id_code": 10, "index_symbol": "NIFTY PVT BANK"},
    {"key": "fmcg", "name": "FMCG", "security_id_code": 20, "index_symbol": "NIFTY FMCG"},
    {"key": "it", "name": "Information Technology", "security_id_code": 21, "index_symbol": "NIFTY IT"},
    {"key": "media", "name": "Media", "security_id_code": 22, "index_symbol": "NIFTY MEDIA"},
    {"key": "metal", "name": "Metals", "security_id_code": 23, "index_symbol": "NIFTY METAL"},
    {"key": "pharma", "name": "Pharma", "security_id_code": 24, "index_symbol": "NIFTY PHARMA"},
    {"key": "psu-bank", "name": "PSU Banks", "security_id_code": 25, "index_symbol": "NIFTY PSU BANK"},
    {"key": "realty", "name": "Realty", "security_id_code": 26, "index_symbol": "NIFTY REALTY"},
    {"key": "energy", "name": "Energy", "security_id_code": 33, "index_symbol": "NIFTY ENERGY"},
    {"key": "infrastructure", "name": "Infrastructure", "security_id_code": 34, "index_symbol": "NIFTY INFRA"},
    {"key": "mnc", "name": "MNC", "security_id_code": 35, "index_symbol": "NIFTY MNC"},
    {"key": "services", "name": "Services", "security_id_code": 37, "index_symbol": "NIFTY SERV SECTOR"},
    {"key": "consumer-durables", "name": "Consumer Durables", "security_id_code": 59, "index_symbol": "NIFTY CONSUMER DURABLES"},
    {"key": "financial-services", "name": "Financial Services", "security_id_code": 60, "index_symbol": "NIFTY FINANCIAL SERVICES"},
    {"key": "oil-gas", "name": "Oil & Gas", "security_id_code": 61, "index_symbol": "NIFTY OIL AND GAS"},
    {"key": "healthcare", "name": "Healthcare", "security_id_code": 62, "index_symbol": "NIFTY HEALTHCARE"},
)
_SECTOR_BY_KEY = {item["key"]: item for item in SECTOR_UNIVERSES}
_sector_cache = {}
_sector_cache_lock = threading.Lock()
SECTOR_CACHE_TTL_SECONDS = 45


def _fetch_sector_movers_uncached(sector):
    """Fetch only the provider-ranked gainers and losers for one selected sector."""
    movers = {"gainers": [], "losers": []}
    errors = []

    for mover_type, type_flag in (("gainers", "G"), ("losers", "L")):
        try:
            response = _fetch_mstock_movers(
                exchange=1,
                security_id_code=sector["security_id_code"],
                segment=1,
                type_flag=type_flag,
            )
            for raw in extract_type_a_mover_rows(response):
                if not isinstance(raw, dict):
                    continue
                item = normalize_mover(raw)
                if str(item.get("exchange") or "NSE").upper() != "NSE":
                    continue
                if not item.get("symbol"):
                    continue
                item["exchange"] = "NSE"
                item["sector"] = sector["name"]
                movers[mover_type].append(item)
        except Exception as exc:
            errors.append({
                "source": "m.Stock",
                "sector": sector["key"],
                "type": mover_type,
                "message": str(exc),
            })

    sector_index = None
    try:
        sector_index = fetch_index({
            "name": sector["name"],
            "exchange": "NSE",
            "symbol": sector["index_symbol"],
        })
    except Exception as exc:
        errors.append({
            "source": "m.Stock index quote",
            "sector": sector["key"],
            "type": "sector_index",
            "message": str(exc),
        })

    if errors and not movers["gainers"] and not movers["losers"]:
        raise HTTPException(
            status_code=502,
            detail={"message": "Unable to retrieve sector movers.", "errors": errors},
        )

    return {
        "status": "partial" if errors else "success",
        "sector": {
            "key": sector["key"],
            "name": sector["name"],
            "security_id_code": sector["security_id_code"],
            "index_symbol": sector["index_symbol"],
        },
        "scope": {
            "exchange": "NSE",
            "universe": "Provider-ranked gainers and losers for the selected NSE sector index",
            "note": "These are the provider's top movers within the selected sector, not every sector constituent.",
        },
        "movers": movers,
        "sector_index": sector_index,
        "counts": {
            "gainers": len(movers["gainers"]),
            "losers": len(movers["losers"]),
            "total_returned": len(movers["gainers"]) + len(movers["losers"]),
        },
        "capabilities": {
            "sector_gainer_loser_lists": True,
            "full_sector_constituent_breadth": False,
            "sector_index_quote": sector_index is not None,
        },
        "limitations": [
            "The provider response contains ranked movers, not the complete sector constituent universe.",
            "The existing index-quote contract supplies a current index price only; percentage performance is unavailable unless returned by the provider.",
        ],
        "data_sources": {
            "primary": "m.Stock Type A Top Gainers and Losers API",
            "security_id_code": sector["security_id_code"],
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "errors": errors,
        "read_only": True,
        "database_write": False,
    }


def _get_cached_sector_movers(sector):
    now = time.monotonic()
    cached = _sector_cache.get(sector["key"])
    if cached and now - cached["loaded_at"] < SECTOR_CACHE_TTL_SECONDS:
        return cached["payload"]
    # Serialize cache misses so concurrent selections do not duplicate provider
    # calls and breach m.Stock's documented request-rate limit.
    with _sector_cache_lock:
        now = time.monotonic()
        cached = _sector_cache.get(sector["key"])
        if cached and now - cached["loaded_at"] < SECTOR_CACHE_TTL_SECONDS:
            return cached["payload"]
        payload = _fetch_sector_movers_uncached(sector)
        _sector_cache[sector["key"]] = {"loaded_at": time.monotonic(), "payload": payload}
        return payload


@router.get("/")
def get_market_flow_snapshot(sector: str | None = None):
    if sector is not None:
        sector_config = _SECTOR_BY_KEY.get(str(sector).strip().lower())
        if sector_config is None:
            raise HTTPException(status_code=404, detail="Unsupported Chart Flow sector.")
        return _get_cached_sector_movers(sector_config)

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
        "sector_universes": [
            {key: item[key] for key in ("key", "name", "security_id_code", "index_symbol")}
            for item in SECTOR_UNIVERSES
        ],
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
