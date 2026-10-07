# ============================================================
# FINANCIAL OS
# MARKET DATA API
# ============================================================
#
# This API is the Financial OS gateway to market data.
#
# Frontend / Application
#          ↓
#     Financial OS API
#          ↓
#     Market Provider
#          ↓
#     Alpha Vantage
#
# IMPORTANT:
# The frontend NEVER calls Alpha Vantage directly.
#
# ============================================================

from fastapi import APIRouter, HTTPException

from app.services.market_price import (
    MarketPriceError,
    get_market_price,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/market",
    tags=["Market Data"],
)


# ============================================================
# MARKET API STATUS
# ============================================================

@router.get("/status")
def market_status():
    """
    Check whether the Financial OS market-data service
    is available.

    This does NOT call Alpha Vantage.
    """

    return {
        "status": "online",
        "service": "Financial OS Market Data API",
        "provider": "Alpha Vantage",
    }


# ============================================================
# GET MARKET QUOTE
# ============================================================

@router.get("/quote")
def market_quote(symbol: str):
    """
    Get the latest available market price for a symbol.

    Example:

    /api/market/quote?symbol=IBM

    The frontend calls this endpoint.

    The backend then calls Alpha Vantage.
    """

    # --------------------------------------------------------
    # Validate symbol
    # --------------------------------------------------------

    symbol = symbol.strip().upper()

    if not symbol:

        raise HTTPException(
            status_code=400,
            detail="Market symbol is required.",
        )

    # --------------------------------------------------------
    # Fetch market price
    # --------------------------------------------------------

    try:

        price = get_market_price(symbol)

    except MarketPriceError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # --------------------------------------------------------
    # Return normalized Financial OS response
    # --------------------------------------------------------

    return {
        "status": "success",
        "symbol": symbol,
        "price": price,
        "provider": "Alpha Vantage",
    }
