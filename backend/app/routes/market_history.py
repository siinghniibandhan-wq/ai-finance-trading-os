"""
Financial OS — Historical Market Data Engine v1.0

Purpose:
- Provide historical OHLCV market data to Financial OS.
- Use the existing AWS m.Stock Gateway.
- Keep historical-data logic separate from market.py.
- Read-only.
- No database writes.
- Uses Python standard library only.

Flow:

Client
   ↓
Financial OS Historical Market Data Engine
   ↓
AWS m.Stock Gateway /historical
   ↓
m.Stock Historical Market Data
"""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query


# ============================================================
# CONFIGURATION
# ============================================================

MSTOCK_GATEWAY_URL = "http://54.153.201.74:8000"


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/market-history",
    tags=["Market History"],
)


# ============================================================
# HISTORICAL MARKET DATA
# ============================================================

@router.get("/")
def get_market_history(
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
    cleaned_symbol = symbol.strip().upper()
    cleaned_exchange = exchange.strip().upper()
    cleaned_interval = interval.strip().lower()
    cleaned_from = from_date.strip()
    cleaned_to = to_date.strip()

    # --------------------------------------------------------
    # Validate symbol
    # --------------------------------------------------------

    if not cleaned_symbol:
        raise HTTPException(
            status_code=400,
            detail="Market symbol is required.",
        )

    # --------------------------------------------------------
    # Validate exchange
    # --------------------------------------------------------

    allowed_exchanges = {
        "NSE",
        "NFO",
        "BSE",
        "BFO",
    }

    if cleaned_exchange not in allowed_exchanges:
        raise HTTPException(
            status_code=400,
            detail="Unsupported exchange.",
        )

    # --------------------------------------------------------
    # Validate interval
    # --------------------------------------------------------

    allowed_intervals = {
        "minute",
        "day",
        "3minute",
        "5minute",
        "10minute",
        "15minute",
        "30minute",
        "60minute",
    }

    if cleaned_interval not in allowed_intervals:
        raise HTTPException(
            status_code=400,
            detail="Unsupported historical interval.",
        )

    # --------------------------------------------------------
    # Basic date validation
    # --------------------------------------------------------

    if len(cleaned_from) != 10 or len(cleaned_to) != 10:
        raise HTTPException(
            status_code=400,
            detail="Dates must use YYYY-MM-DD format.",
        )

    # --------------------------------------------------------
    # Resolve symbol through Market Search
    #
    # The AWS historical endpoint requires an instrument token.
    # We first use the existing instrument master.
    # --------------------------------------------------------

    search_url = (
        f"{MSTOCK_GATEWAY_URL}/instruments"
    )

    try:
        search_request = Request(
            search_url,
            method="GET",
        )

        with urlopen(
            search_request,
            timeout=30,
        ) as response:

            if response.status != 200:
                raise HTTPException(
                    status_code=502,
                    detail="Market instrument data unavailable.",
                )

            csv_text = response.read().decode(
                "utf-8",
                errors="replace",
            )

    except HTTPError as exc:
        if exc.code == 401:
            raise HTTPException(
                status_code=502,
                detail="Market gateway authentication required.",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve market instrument data.",
        ) from exc

    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach market data gateway.",
        ) from exc

    # --------------------------------------------------------
    # Find instrument token
    # --------------------------------------------------------

    import csv
    from io import StringIO

    reader = csv.DictReader(
        StringIO(csv_text)
    )

    instrument_token = None
    resolved_symbol = None
    resolved_name = None

    for row in reader:

        row_exchange = (
            (row.get("exchange") or "")
            .strip()
            .upper()
        )

        row_symbol = (
            (row.get("tradingsymbol") or "")
            .strip()
            .upper()
        )

        if (
            row_exchange == cleaned_exchange
            and row_symbol == cleaned_symbol
        ):
            instrument_token = (
                row.get("instrument_token")
            )

            resolved_symbol = (
                row.get("tradingsymbol")
            )

            resolved_name = (
                row.get("name")
            )

            break

    if not instrument_token:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Market symbol '{cleaned_symbol}' "
                f"was not found on {cleaned_exchange}."
            ),
        )

    # --------------------------------------------------------
    # Request historical data from AWS gateway
    # --------------------------------------------------------

    historical_url = (
        f"{MSTOCK_GATEWAY_URL}/historical/"
        f"{cleaned_exchange}/"
        f"{instrument_token}/"
        f"{cleaned_interval}"
    )

    query_string = urlencode({
        "from": cleaned_from,
        "to": cleaned_to,
    })

    try:
        historical_request = Request(
            f"{historical_url}?{query_string}",
            method="GET",
        )

        with urlopen(
            historical_request,
            timeout=30,
        ) as response:

            status_code = response.status

            response_text = response.read().decode(
                "utf-8",
                errors="replace",
            )

    except HTTPError as exc:

        if exc.code == 401:
            raise HTTPException(
                status_code=502,
                detail="Market gateway authentication required.",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="Historical market data unavailable.",
        ) from exc

    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach market data gateway.",
        ) from exc

    # --------------------------------------------------------
    # Validate gateway response
    # --------------------------------------------------------

    if status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Historical market data request failed.",
        )

    try:
        provider_data = json.loads(
            response_text
        )

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Invalid historical market data response.",
        ) from exc

    if provider_data.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail=provider_data.get(
                "message",
                "Historical market data request failed.",
            ),
        )

    # --------------------------------------------------------
    # Extract candles
    # --------------------------------------------------------

    data = provider_data.get("data") or {}

    candles = data.get(
        "candles",
        [],
    )

    # --------------------------------------------------------
    # Financial OS response
    # --------------------------------------------------------

    return {
        "status": "success",
        "engine": "Historical Market Data Engine",
        "version": "1.0",
        "read_only": True,
        "instrument": {
            "symbol": resolved_symbol,
            "name": resolved_name,
            "exchange": cleaned_exchange,
            "instrument_token": int(
                instrument_token
            ),
        },
        "request": {
            "interval": cleaned_interval,
            "from": cleaned_from,
            "to": cleaned_to,
        },
        "count": len(candles),
        "candles": candles,
        "source": {
            "provider": "m.Stock",
            "gateway": "AWS Gateway",
            "endpoint": "/historical",
        },
        "database_write": False,
        "next_module": "Market Charts",
    }
