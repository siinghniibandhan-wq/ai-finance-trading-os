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

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.routes.market import (
    get_market_price,
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

        price = get_market_price(
            cleaned_symbol
        )

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

        "last_updated": datetime.now(
            timezone.utc
        ).isoformat(),

        "database_write": False,

        "next_module": "Market Search Engine",
    }
