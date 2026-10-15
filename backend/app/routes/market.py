# ============================================================
# FINANCIAL OS
# MARKET DATA API
# ============================================================
#
# This route uses the Financial OS market-price service.
#
# Flow:
#
# Financial OS API
#       ↓
# market.py
#       ↓
# market_price.py
#       ↓
# AWS m.Stock Gateway
#       ↓
# m.Stock
#       ↓
# NSE / BSE market price
#
# IMPORTANT:
# - No m.Stock API key here
# - No TOTP here
# - No access token here
# - No Alpha Vantage here
# ============================================================


from fastapi import APIRouter, HTTPException

from app.services.market_price import (
    MarketPriceError,
    get_market_price,
    get_market_quote,
)


# ============================================================
# ROUTER CONFIGURATION
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
    Check the Financial OS Market Data API.

    This endpoint does not call m.Stock.
    It only reports the configured provider.
    """

    return {
        "status": "online",
        "service": "Financial OS Market Data API",
        "provider": "m.Stock",
        "gateway": "AWS m.Stock Gateway",
    }


# ============================================================
# MARKET QUOTE
# ============================================================

@router.get("/quote")
def market_quote(symbol: str):
    """
    Get the latest market price for an investment symbol.

    Example:

        /api/market/quote?symbol=RELIANCE

    The market-price service handles communication with
    the AWS m.Stock Gateway.
    """

    # --------------------------------------------------------
    # Clean symbol
    # --------------------------------------------------------

    symbol = symbol.strip().upper()

    # --------------------------------------------------------
    # Validate symbol
    # --------------------------------------------------------

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Market symbol is required.",
        )

    # --------------------------------------------------------
    # Get latest market price
    # --------------------------------------------------------

    try:

        quote_data = get_market_quote(symbol)
        price = quote_data["price"]

    except MarketPriceError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # --------------------------------------------------------
    # Return successful response
    # --------------------------------------------------------

    return {
        "status": "success",
        "symbol": symbol,
        "price": price,
        "provider": "m.Stock",
        "source": "AWS m.Stock Gateway",
        "retrieved_at": quote_data["retrieved_at"],
        "cache_hit": quote_data["cache_hit"],
        "cache_age_seconds": quote_data["cache_age_seconds"],
        "provider_latency_ms": quote_data["provider_latency_ms"],
        "provider_market_timestamp": None,
    }
