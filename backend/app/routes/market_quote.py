"""
Financial OS — Market Quote Engine v1.0

Purpose:
- Provide a clean API for fetching a live market quote.
- Reuse the existing market.py provider service.
- Keep AWS / m.Stock authentication outside this route.
- Read-only.
- No database writes.

Flow:

Client
   ↓
Market Quote Engine
   ↓
market.py
   ↓
AWS m.Stock Gateway
   ↓
Live Quote
"""

from fastapi import APIRouter, HTTPException, Query

from app.services.market_price import (
    get_market_quote,
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

    # --------------------------------------------------------
    # FETCH LIVE PRICE
    # --------------------------------------------------------

    try:

        quote_data = get_market_quote(cleaned_symbol)
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

        "quote": {
            "last_price": float(price),
        },

        "source": {
            "provider": "m.Stock",
            "gateway": "AWS Gateway",
            "service": "market.py",
        },

        # Original gateway retrieval time, not this response's time.
        "last_updated": quote_data["retrieved_at"],
        "retrieved_at": quote_data["retrieved_at"],
        "cache_hit": quote_data["cache_hit"],
        "provider_market_timestamp": None,
        "freshness_note": (
            "Timestamp indicates backend gateway retrieval time; the provider's "
            "original market timestamp is not available from the current gateway response."
        ),

        "database_write": False,

        "next_module": "Market Search Engine",
    }
