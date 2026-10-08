"""
Financial OS — Market Search Engine v1.0

Purpose:
- Search the m.Stock instrument master.
- Keep market-search logic separate from market.py.
- Use the existing AWS m.Stock Gateway.
- Read-only.
- No database writes.

Flow:

Client
   ↓
Financial OS Market Search Engine
   ↓
AWS m.Stock Gateway /instruments
   ↓
m.Stock Script Master
"""

from io import StringIO

import pandas as pd
import requests
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
        response = requests.get(
            f"{MSTOCK_GATEWAY_URL}/instruments",
            timeout=30,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach market data gateway.",
        ) from exc

    # --------------------------------------------------------
    # Gateway authentication
    # --------------------------------------------------------

    if response.status_code == 401:
        raise HTTPException(
            status_code=502,
            detail="Market gateway authentication required.",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Market instrument data unavailable.",
        )

    # --------------------------------------------------------
    # Parse Script Master CSV
    # --------------------------------------------------------

    try:
        dataframe = pd.read_csv(
            StringIO(response.text)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to parse market instrument data.",
        ) from exc

    # --------------------------------------------------------
    # Exchange filter
    # --------------------------------------------------------

    if "exchange" in dataframe.columns:
        dataframe = dataframe[
            dataframe["exchange"]
            .fillna("")
            .astype(str)
            .str.upper()
            == cleaned_exchange
        ]

    # --------------------------------------------------------
    # Search symbol OR company name
    # --------------------------------------------------------

    symbol_match = (
        dataframe["tradingsymbol"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.contains(
            cleaned_query,
            regex=False,
        )
    )

    name_match = (
        dataframe["name"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.contains(
            cleaned_query,
            regex=False,
        )
    )

    dataframe = dataframe[
        symbol_match | name_match
    ]

    # --------------------------------------------------------
    # Limit results
    # --------------------------------------------------------

    dataframe = dataframe.head(limit)

    # --------------------------------------------------------
    # Convert to API response
    # --------------------------------------------------------

    results = []

    for _, row in dataframe.iterrows():

        results.append({
            "instrument_token": (
                int(row["instrument_token"])
                if pd.notna(row.get("instrument_token"))
                else None
            ),
            "symbol": (
                str(row["tradingsymbol"])
                if pd.notna(row.get("tradingsymbol"))
                else None
            ),
            "name": (
                str(row["name"])
                if pd.notna(row.get("name"))
                else None
            ),
            "exchange": (
                str(row["exchange"])
                if pd.notna(row.get("exchange"))
                else None
            ),
            "instrument_type": (
                str(row["instrument_type"])
                if pd.notna(row.get("instrument_type"))
                else None
            ),
            "last_price": (
                float(row["last_price"])
                if pd.notna(row.get("last_price"))
                else None
            ),
        })

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
