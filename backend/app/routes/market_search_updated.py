"""
Financial OS — Market Search Engine v1.0

Purpose:
- Search the m.Stock instrument master.
- Keep market-search logic separate from market.py.
- Use the existing AWS m.Stock Gateway.
- Read-only.
- No database writes.
- Uses Python standard library only.

Flow:

Client
   ↓
Financial OS Market Search Engine
   ↓
AWS m.Stock Gateway /instruments
   ↓
m.Stock Script Master
"""

import csv
from io import StringIO
from urllib.error import HTTPError, URLError
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
    prefix="/api/market-search",
    tags=["Market Search"],
)


# ============================================================
# MARKET SEARCH
# ============================================================

@router.get("/")
def search_market(
    query: str = Query(
        ...,
        min_length=1,
        description="Search symbol or company name",
    ),
    exchange: str = Query(
        "NSE",
        description="Exchange filter",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=50,
        description="Maximum number of results",
    ),
):
    cleaned_query = query.strip().upper()
    cleaned_exchange = exchange.strip().upper()

    if not cleaned_query:
        raise HTTPException(
            status_code=400,
            detail="Search query is required.",
        )

    # --------------------------------------------------------
    # Fetch instrument master from AWS gateway
    # --------------------------------------------------------

    try:
        request = Request(
            f"{MSTOCK_GATEWAY_URL}/instruments",
            method="GET",
        )

        with urlopen(request, timeout=30) as response:
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
            detail="Market instrument data unavailable.",
        ) from exc

    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach market data gateway.",
        ) from exc

    # --------------------------------------------------------
    # Gateway authentication
    # --------------------------------------------------------

    if status_code == 401:
        raise HTTPException(
            status_code=502,
            detail="Market gateway authentication required.",
        )

    if status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Market instrument data unavailable.",
        )

    # --------------------------------------------------------
    # Parse Script Master CSV
    # --------------------------------------------------------

    try:
        reader = csv.DictReader(
            StringIO(response_text)
        )

        results = []

        for row in reader:

            row_exchange = (
                (row.get("exchange") or "")
                .strip()
                .upper()
            )

            if row_exchange != cleaned_exchange:
                continue

            symbol = (
                (row.get("tradingsymbol") or "")
                .strip()
            )

            name = (
                (row.get("name") or "")
                .strip()
            )

            symbol_upper = symbol.upper()
            name_upper = name.upper()

            # ------------------------------------------------
            # Search symbol OR company name
            # ------------------------------------------------

            if (
                cleaned_query not in symbol_upper
                and cleaned_query not in name_upper
            ):
                continue

            # ------------------------------------------------
            # Instrument token
            # ------------------------------------------------

            instrument_token = row.get(
                "instrument_token"
            )

            try:
                instrument_token = (
                    int(instrument_token)
                    if instrument_token
                    else None
                )
            except (ValueError, TypeError):
                instrument_token = None

            # ------------------------------------------------
            # Last price
            # ------------------------------------------------

            last_price = row.get("last_price")

            try:
                last_price = (
                    float(last_price)
                    if last_price
                    else None
                )
            except (ValueError, TypeError):
                last_price = None

            # ------------------------------------------------
            # Add result
            # ------------------------------------------------

            results.append({
                "instrument_token": instrument_token,
                "symbol": symbol or None,
                "name": name or None,
                "exchange": row_exchange or None,
                "instrument_type": (
                    row.get("instrument_type")
                    or None
                ),
                "last_price": last_price,
            })

            # ------------------------------------------------
            # Stop once requested limit is reached
            # ------------------------------------------------

            if len(results) >= limit:
                break

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to parse market instrument data.",
        ) from exc

    # --------------------------------------------------------
    # API response
    # --------------------------------------------------------

    return {
        "status": "success",
        "engine": "Market Search Engine",
        "version": "1.0",
        "read_only": True,
        "query": cleaned_query,
        "exchange": cleaned_exchange,
        "count": len(results),
        "results": results,
        "source": {
            "provider": "m.Stock",
            "gateway": "AWS Gateway",
            "endpoint": "/instruments",
        },
        "database_write": False,
        "next_module": "Historical Market Data",
    }
