"""
Financial OS — Market Charts Engine v1.0

Purpose:
- Provide chart-ready historical market data.
- Reuse the existing Market History Engine.
- Support OHLCV chart data.
- Read-only.
- No database writes.
- Uses existing Financial OS APIs.
"""

from fastapi import APIRouter, HTTPException, Query

from app.routes.market_history import get_market_history


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/market-charts",
    tags=["Market Charts"],
)


# ============================================================
# MARKET CHART
# ============================================================

@router.get("/")
def get_market_chart(
    symbol: str = Query(
        ...,
        min_length=1,
        description="Market symbol, for example RELIANCE",
    ),
    exchange: str = Query(
        "NSE",
        description="Exchange",
    ),
    interval: str = Query(
        "day",
        description="Historical interval",
    ),
    from_date: str = Query(
        ...,
        alias="from",
        description="Start date in YYYY-MM-DD format",
    ),
    to_date: str = Query(
        ...,
        alias="to",
        description="End date in YYYY-MM-DD format",
    ),
):
    # --------------------------------------------------------
    # Reuse the existing Historical Market Data Engine
    # --------------------------------------------------------

    try:
        history = get_market_history(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate market chart data.",
        ) from exc

    # --------------------------------------------------------
    # Convert candles into chart-ready objects
    #
    # m.Stock candle format:
    # [timestamp, open, high, low, close, volume]
    # --------------------------------------------------------

    chart_data = []

    for candle in history.get("candles", []):

        if len(candle) < 6:
            continue

        chart_data.append({
            "timestamp": candle[0],
            "open": candle[1],
            "high": candle[2],
            "low": candle[3],
            "close": candle[4],
            "volume": candle[5],
        })

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "status": "success",
        "engine": "Market Charts Engine",
        "version": "1.0",
        "read_only": True,
        "chart": {
            "type": "candlestick",
            "symbol": history["instrument"]["symbol"],
            "name": history["instrument"]["name"],
            "exchange": history["instrument"]["exchange"],
            "interval": history["request"]["interval"],
            "from": history["request"]["from"],
            "to": history["request"]["to"],
        },
        "count": len(chart_data),
        "data": chart_data,
        "source": {
            "provider": "m.Stock",
            "gateway": "m.Stock Gateway",
            "engine": "Historical Market Data Engine",
        },
        "database_write": False,
        "next_module": "Watchlist Engine",
    }
