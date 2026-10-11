"""
Financial OS — Vibe Trading capability layer (Phase 1)
=====================================================

Additive, read-only market research integration.

Safety and compatibility:
- Reuses the existing market-price service and AWS m.Stock gateway.
- Does not change gateway credentials/configuration.
- Does not write to the database or create investment records.
- Does not submit broker orders.
- Reports retrieval time separately from the provider's market timestamp.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import logging
import os
from threading import Lock
from time import monotonic
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.market_price import MarketPriceError, get_market_price

router = APIRouter(prefix="/api/vibe-trading", tags=["Vibe Trading"])
logger = logging.getLogger(__name__)


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================
def _read_int_setting(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read an integer environment setting safely and clamp it."""
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _read_float_setting(name: str, default: float, minimum: float, maximum: float) -> float:
    """Read a float environment setting safely and clamp it."""
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


QUOTE_CACHE_TTL_SECONDS = _read_float_setting(
    "VIBE_QUOTE_CACHE_TTL_SECONDS", 2.0, 0.0, 30.0
)
QUOTE_WORKERS = _read_int_setting("VIBE_QUOTE_WORKERS", 8, 1, 8)
QUOTE_CACHE_MAX_ENTRIES = 1000

# Cache values: symbol -> (monotonic timestamp, price, retrieved_at ISO timestamp)
QUOTE_CACHE: Dict[str, tuple] = {}
QUOTE_CACHE_LOCK = Lock()


# ============================================================
# CACHED MARKET QUOTE
# ============================================================
def _get_cached_market_price(symbol: str):
    """Use a short cache to reduce duplicate calls to the existing gateway."""
    cleaned = symbol.strip().upper()
    now = monotonic()

    if QUOTE_CACHE_TTL_SECONDS > 0:
        with QUOTE_CACHE_LOCK:
            cached = QUOTE_CACHE.get(cleaned)
            if cached and now - cached[0] <= QUOTE_CACHE_TTL_SECONDS:
                return cached[1], cached[2], True

    # Never hold the cache lock during network I/O.
    price = get_market_price(cleaned)
    retrieved_at = datetime.now(timezone.utc).isoformat()

    if QUOTE_CACHE_TTL_SECONDS > 0:
        with QUOTE_CACHE_LOCK:
            # Keep the cache bounded and remove expired entries if needed.
            if len(QUOTE_CACHE) >= QUOTE_CACHE_MAX_ENTRIES:
                cutoff = monotonic() - QUOTE_CACHE_TTL_SECONDS
                expired = [
                    key for key, value in QUOTE_CACHE.items()
                    if value[0] < cutoff
                ]
                for key in expired:
                    QUOTE_CACHE.pop(key, None)

                # If all entries are still fresh, evict the oldest entry.
                if len(QUOTE_CACHE) >= QUOTE_CACHE_MAX_ENTRIES:
                    oldest_key = min(QUOTE_CACHE, key=lambda key: QUOTE_CACHE[key][0])
                    QUOTE_CACHE.pop(oldest_key, None)

            QUOTE_CACHE[cleaned] = (monotonic(), price, retrieved_at)

    return price, retrieved_at, False


# ============================================================
# NORMALISED QUOTE RESULT
# ============================================================
def _quote_result(symbol: str):
    """Return a per-symbol result, allowing batch requests to be partially successful."""
    cleaned = symbol.strip().upper()
    try:
        price, retrieved_at, cache_hit = _get_cached_market_price(cleaned)
        return {
            "symbol": cleaned,
            "status": "success",
            "quote": {"last_price": float(price)},
            "source": {
                "provider": "m.Stock",
                "gateway": "existing AWS m.Stock Gateway",
            },
            "retrieved_at": retrieved_at,
            "provider_market_timestamp": None,
            "freshness_note": (
                "The current market-price service does not expose the provider's "
                "original quote timestamp. Retrieval time is not proof of real-time data."
            ),
            "cache_hit": cache_hit,
        }
    except MarketPriceError as exc:
        return {"symbol": cleaned, "status": "error", "error": str(exc)}
    except Exception:
        logger.exception("Unexpected Vibe Trading quote error for symbol %s", cleaned)
        return {"symbol": cleaned, "status": "error", "error": "Unable to retrieve quote."}


# ============================================================
# REQUEST MODELS
# ============================================================
class VibeQuotesRequest(BaseModel):
    """Batch quote request: one HTTP request for multiple instruments."""
    symbols: List[str] = Field(..., min_length=1, max_length=20)


class VibeResearchRequest(BaseModel):
    """Small, evidence-grounded market research request."""
    question: str = Field(..., min_length=3, max_length=4000)
    symbols: List[str] = Field(default_factory=list, max_length=20)


# ============================================================
# STATUS
# ============================================================
@router.get("/status")
def vibe_trading_status():
    """Report the currently implemented capabilities without external calls."""
    return {
        "status": "available",
        "module": "Financial OS Vibe Trading",
        "phase": 1,
        "features": [
            "existing_mstock_quote_lookup",
            "parallel_batch_quotes",
            "short_lived_quote_cache",
            "market_aware_ai_research",
        ],
        "market_provider": "m.Stock via existing AWS m.Stock Gateway",
        "ai_provider": "Google Gemini",
        "read_only": True,
        "live_order_execution": False,
    }


# ============================================================
# SINGLE QUOTE
# ============================================================
@router.get("/quote")
def vibe_market_quote(
    symbol: str = Query(..., min_length=1, max_length=80),
):
    """Fetch one quote through the existing gateway-backed service."""
    cleaned_symbol = symbol.strip().upper()
    if not cleaned_symbol:
        raise HTTPException(status_code=400, detail="Market symbol is required.")

    result = _quote_result(cleaned_symbol)
    if result["status"] != "success":
        raise HTTPException(status_code=502, detail=result["error"])

    return {**result, "read_only": True}


# ============================================================
# BATCH QUOTES
# ============================================================
@router.post("/quotes")
def vibe_market_quotes(request: VibeQuotesRequest):
    """Fetch several symbols concurrently and preserve the caller's symbol order."""
    symbols = list(dict.fromkeys(
        symbol.strip().upper()
        for symbol in request.symbols
        if isinstance(symbol, str) and symbol.strip()
    ))
    if not symbols:
        raise HTTPException(status_code=400, detail="At least one valid symbol is required.")

    results = {}
    with ThreadPoolExecutor(max_workers=min(QUOTE_WORKERS, len(symbols))) as executor:
        futures = {executor.submit(_quote_result, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                results[symbol] = future.result()
            except Exception:
                logger.exception("Batch quote worker failed for symbol %s", symbol)
                results[symbol] = {
                    "symbol": symbol,
                    "status": "error",
                    "error": "Unable to retrieve quote.",
                }

    ordered = [results[symbol] for symbol in symbols]
    success_count = sum(item["status"] == "success" for item in ordered)
    status = (
        "success" if success_count == len(ordered)
        else "partial" if success_count
        else "error"
    )
    return {
        "status": status,
        "count": len(ordered),
        "success_count": success_count,
        "failed_count": len(ordered) - success_count,
        "quotes": ordered,
        "read_only": True,
    }


# ============================================================
# MARKET-AWARE AI RESEARCH
# ============================================================
@router.post("/research")
def vibe_market_research(request: VibeResearchRequest):
    """Ask Gemini to analyse requested symbols using only quotes actually retrieved."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured. Add GEMINI_API_KEY to backend environment variables.",
        )

    symbols = list(dict.fromkeys(
        symbol.strip().upper()
        for symbol in request.symbols
        if isinstance(symbol, str) and symbol.strip()
    ))

    quote_results = {}
    if symbols:
        with ThreadPoolExecutor(max_workers=min(QUOTE_WORKERS, len(symbols))) as executor:
            futures = {executor.submit(_quote_result, symbol): symbol for symbol in symbols}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    quote_results[symbol] = future.result()
                except Exception:
                    logger.exception("Research quote worker failed for symbol %s", symbol)
                    quote_results[symbol] = {
                        "symbol": symbol,
                        "status": "error",
                        "error": "Unable to retrieve quote.",
                    }

    retrieved_quotes = []
    quote_errors = []
    for symbol in symbols:
        result = quote_results[symbol]
        if result["status"] == "success":
            retrieved_quotes.append({
                "symbol": symbol,
                "last_price": result["quote"]["last_price"],
                "provider": "m.Stock via existing AWS m.Stock Gateway",
                "retrieved_at": result["retrieved_at"],
                "provider_market_timestamp": None,
                "cache_hit": result["cache_hit"],
            })
        else:
            quote_errors.append({"symbol": symbol, "error": result["error"]})

    if symbols and not retrieved_quotes:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "No requested market quotes could be retrieved; research was not run.",
                "quote_errors": quote_errors,
            },
        )

    evidence = {
        "quotes": retrieved_quotes,
        "quote_errors": quote_errors,
        "note": (
            "Only successfully retrieved quote values are supplied. The current service does not "
            "expose the exchange/provider timestamp. Do not present retrieval time as proof of "
            "real-time pricing. No quote data was supplied if the symbol list is empty."
        ),
    }

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            contents=(
                "You are the market-research component of Financial OS Vibe Trading. "
                "Use only supplied evidence for claims about current prices. Never invent prices, "
                "timestamps, fundamentals, news, or backtest results. State when evidence is missing. "
                "Distinguish research from a trade instruction and do not claim to place orders. "
                "This endpoint is research-only.\n\n"
                f"User research question: {request.question.strip()}\n\n"
                f"Retrieved market evidence (JSON): {evidence}"
            ),
        )
        answer: Optional[str] = getattr(response, "text", None)
        if not answer:
            raise ValueError("Gemini returned no text.")
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gemini SDK is missing. Install google-genai in backend requirements.",
        ) from exc
    except Exception as exc:
        logger.exception("Vibe Trading research failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="AI research failed. Check backend logs.",
        ) from exc

    return {
        "status": "success",
        "module": "Financial OS Vibe Trading",
        "mode": "research_only",
        "answer": answer,
        "market_evidence": evidence,
        "broker_orders_submitted": False,
        "database_write": False,
    }
