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
import os
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query


# ============================================================
# CONFIGURATION
# ============================================================

MSTOCK_GATEWAY_URL = os.getenv(
    "MSTOCK_GATEWAY_URL",
    "http://54.153.201.74:8000",
).rstrip("/")


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
        "ALL",
        description="Exchange filter: ALL, NSE, or BSE",
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
    if cleaned_exchange not in {"ALL", "NSE", "BSE"}:
        raise HTTPException(status_code=422, detail="Exchange must be ALL, NSE, or BSE.")

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

            if row_exchange not in {"NSE", "BSE"}:
                continue
            if cleaned_exchange != "ALL" and row_exchange != cleaned_exchange:
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

            instrument_type = (row.get("instrument_type") or "").strip()
            segment = (row.get("segment") or "").strip()
            expiry = (row.get("expiry") or "").strip() or None
            strike = (row.get("strike") or "").strip() or None
            lot_size = (row.get("lot_size") or "").strip() or None
            # Exchange series is commonly encoded in the trading symbol (e.g. -EQ)
            # or provided separately by a provider-specific master.
            symbol_suffix = symbol.rsplit("-", 1)[-1].upper() if "-" in symbol else ""
            series = (row.get("series") or "").strip().upper() or (symbol_suffix if symbol_suffix in {"EQ", "BE", "BZ", "SM", "ST", "A", "B", "T"} else "")
            base_symbol = symbol.rsplit("-", 1)[0].upper() if symbol_suffix in {"EQ", "BE", "BZ", "SM", "ST", "A", "B", "T"} else symbol.upper()
            query_symbol = cleaned_query.replace(" ", "")
            normalized_name = "".join(name_upper.split())
            exact_symbol = base_symbol.replace(" ", "") == query_symbol or symbol_upper.replace(" ", "") == query_symbol
            exact_name = normalized_name == "".join(cleaned_query.split())
            starts_match = base_symbol.startswith(cleaned_query) or symbol_upper.startswith(cleaned_query) or name_upper.startswith(cleaned_query)
            results.append({
                "instrument_token": instrument_token,
                "exchange_token": (row.get("exchange_token") or "").strip() or None,
                "symbol": symbol or None,
                "tradingsymbol": symbol or None,
                "name": name or None,
                "exchange": row_exchange or None,
                "series": series or None,
                "segment": segment or None,
                "instrument_type": instrument_type or None,
                "expiry": expiry,
                "strike": strike,
                "lot_size": lot_size,
                "last_price": last_price,
                "_rank": (0 if exact_symbol else 1 if exact_name else 2 if starts_match else 3),
            })

        # Exact symbol/company matches from both exchanges come first, followed
        # by other prefix matches and then broader partial matches.
        results.sort(key=lambda item: (item["_rank"], 0 if item["exchange"] == "NSE" else 1, item["symbol"] or ""))
        results = results[:limit]
        for item in results:
            item.pop("_rank", None)

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
