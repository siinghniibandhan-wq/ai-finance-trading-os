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
        # Instrument-master providers may change CSV header names or include a
        # UTF-8 BOM. Normalize headers once so a valid master does not silently
        # produce zero search results when it uses exch_seg / symbol / company_name.
        reader = csv.DictReader(StringIO(response_text.lstrip("\ufeff")))
        if not reader.fieldnames:
            raise ValueError("Instrument master CSV has no header row.")
        reader.fieldnames = [
            str(field or "").strip().lower().replace(" ", "_")
            for field in reader.fieldnames
        ]

        def field_value(row, *names):
            for field_name in names:
                value = row.get(field_name)
                if value is not None and str(value).strip():
                    return str(value).strip()
            return ""

        results = []

        for row in reader:
            row_exchange = field_value(
                row, "exchange", "exch_seg", "exchange_segment", "exchange_name"
            ).upper()
            if row_exchange.startswith("NSE"):
                row_exchange = "NSE"
            elif row_exchange.startswith("BSE"):
                row_exchange = "BSE"

            if row_exchange not in {"NSE", "BSE"}:
                continue
            if cleaned_exchange != "ALL" and row_exchange != cleaned_exchange:
                continue

            symbol = field_value(
                row, "tradingsymbol", "trading_symbol", "symbol", "ticker"
            )
            name = field_value(
                row, "name", "company_name", "company", "instrument_name", "description"
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

            instrument_token = field_value(row, "instrument_token", "token", "security_id")

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

            last_price = field_value(row, "last_price", "ltp", "close", "price")

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

            instrument_type = field_value(row, "instrument_type", "instrumenttype", "type")
            segment = field_value(row, "segment", "exchange_segment", "exch_seg")
            expiry = field_value(row, "expiry", "expiry_date") or None
            strike = field_value(row, "strike", "strike_price") or None
            lot_size = field_value(row, "lot_size", "lotsize") or None
            # Exchange series is commonly encoded in the trading symbol (e.g. -EQ)
            # or provided separately by a provider-specific master.
            symbol_suffix = symbol.rsplit("-", 1)[-1].upper() if "-" in symbol else ""
            series = field_value(row, "series", "security_series").upper() or (symbol_suffix if symbol_suffix in {"EQ", "BE", "BZ", "SM", "ST", "A", "B", "T"} else "")
            base_symbol = symbol.rsplit("-", 1)[0].upper() if symbol_suffix in {"EQ", "BE", "BZ", "SM", "ST", "A", "B", "T"} else symbol.upper()
            query_symbol = cleaned_query.replace(" ", "")
            normalized_name = "".join(name_upper.split())
            exact_symbol = base_symbol.replace(" ", "") == query_symbol or symbol_upper.replace(" ", "") == query_symbol
            exact_name = normalized_name == "".join(cleaned_query.split())
            starts_match = base_symbol.startswith(cleaned_query) or symbol_upper.startswith(cleaned_query) or name_upper.startswith(cleaned_query)
            results.append({
                "instrument_token": instrument_token,
                "exchange_token": field_value(row, "exchange_token", "exchange_token_id") or None,
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
