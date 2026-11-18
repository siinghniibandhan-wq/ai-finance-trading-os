"""
Financial OS — Market Quote Engine v1.0

Purpose:
- Provide a clean API for fetching a live market quote.
- Reuse the existing market.py provider service.
- Keep m.Stock authentication outside this route.
- Read-only.
- No database writes.

Flow:

Client
   ↓
Market Quote Engine
   ↓
market.py
   ↓
m.Stock Gateway
   ↓
Live Quote
"""

from fastapi import APIRouter, HTTPException, Query

from app.services.market_price import (
    get_market_quote as fetch_market_quote,
    MarketPriceError,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/market-quote",
    tags=["Market Quote"],
)


# ============================================================
# MARKET QUOTE
# ============================================================

@router.get("/")
def get_market_quote(
    symbol: str = Query(
        ...,
        description="Market symbol, for example RELIANCE",
    ),
    exchange: str | None = Query(
        None,
        description="Listing exchange: NSE or BSE (defaults to NSE for unqualified symbols)",
    ),
):
    """
    Fetch the latest market price for a symbol.

    This endpoint does not write to the database.
    """

    # --------------------------------------------------------
    # NORMALIZE INPUT
    # --------------------------------------------------------

    cleaned_symbol = symbol.strip().upper()

    if not cleaned_symbol:
        raise HTTPException(
            status_code=400,
            detail="Market symbol is required.",
        )

    requested_exchange = exchange.strip().upper() if exchange else None
    if requested_exchange is not None and requested_exchange not in {"NSE", "BSE"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported exchange. Use NSE or BSE.",
        )

    # Respect an already-qualified symbol, but reject an explicit exchange conflict.
    if ":" in cleaned_symbol:
        prefix, _ = cleaned_symbol.split(":", 1)
        if prefix in {"NSE", "BSE"} and requested_exchange and prefix != requested_exchange:
            raise HTTPException(
                status_code=400,
                detail="Symbol exchange conflicts with the exchange parameter.",
            )
        quote_symbol = cleaned_symbol
        cleaned_exchange = prefix if prefix in {"NSE", "BSE"} else (requested_exchange or "NSE")
    else:
        cleaned_exchange = requested_exchange or "NSE"
        quote_symbol = f"{cleaned_exchange}:{cleaned_symbol}"

    # --------------------------------------------------------
    # FETCH LIVE PRICE
    # --------------------------------------------------------

    try:

        quote_data = fetch_market_quote(quote_symbol)
        price = quote_data["price"]

    except MarketPriceError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch market quote.",
        ) from exc

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "status": "success",
        "engine": "Market Quote Engine",
        "version": "1.0",
        "read_only": True,

        "symbol": cleaned_symbol,
        "exchange": cleaned_exchange,

        "quote": {
            "last_price": float(price),
            **{
                key: value
                for key, value in (quote_data.get("details") or {}).items()
                if key != "last_price"
            },
        },

        "source": {
            "provider": "m.Stock",
            "gateway": "m.Stock Gateway",
            "service": "market.py",
        },

        # Original gateway retrieval time, not this response's time.
        "last_updated": quote_data["retrieved_at"],
        "retrieved_at": quote_data["retrieved_at"],
        "cache_hit": quote_data["cache_hit"],
        "cache_age_seconds": quote_data.get("cache_age_seconds", 0.0),
        "provider_latency_ms": quote_data.get("provider_latency_ms"),
        "provider_market_timestamp": (
            (quote_data.get("details") or {}).get("exchange_timestamp")
            or (quote_data.get("details") or {}).get("exchange_time")
            or (quote_data.get("details") or {}).get("last_traded_timestamp")
            or (quote_data.get("details") or {}).get("last_traded_time")
            or (quote_data.get("details") or {}).get("timestamp")
        ),
        "freshness_note": (
            "Provider market timestamp is supplied by the broker."
            if any((quote_data.get("details") or {}).get(key) for key in (
                "exchange_timestamp", "exchange_time", "last_traded_timestamp",
                "last_traded_time", "timestamp"
            ))
            else "Provider market timestamp is unavailable; retrieved_at records when the gateway returned this quote."
        ),

        "database_write": False,

        "next_module": "Market Search Engine",
    }
