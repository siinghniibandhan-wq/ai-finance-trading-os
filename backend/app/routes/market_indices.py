"""
Market Indices Engine v1.0
Fetches NIFTY 50 and SENSEX through the existing m.Stock gateway.
Read-only: does not write to the database.
"""

import json
import os
import math
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException

from app.services.mstock_gateway import MSTOCK_GATEWAY_URL, MSTOCK_GATEWAY_SECRET

# --------------------------------------------------
# Router configuration
# --------------------------------------------------

router = APIRouter(
    prefix="/api/market-indices",
    tags=["Market Indices"],
)

# --------------------------------------------------
# Existing m.Stock gateway configuration
# --------------------------------------------------

GATEWAY_URL = MSTOCK_GATEWAY_URL

# Request the four benchmarks required by the Market Workspace.
# The gateway is queried independently per index; unsupported symbols are
# reported in `errors` and do not prevent the other indices from loading.
# Provider support for NIFTY BANK and INDIA VIX must be confirmed by live tests.
SUPPORTED_INDICES = [
    {"name": "NIFTY 50", "exchange": "NSE", "symbol": "NIFTY 50"},
    {"name": "SENSEX", "exchange": "BSE", "symbol": "SENSEX"},
    {"name": "NIFTY BANK", "exchange": "NSE", "symbol": "NIFTY BANK"},
    {"name": "INDIA VIX", "exchange": "NSE", "symbol": "INDIA VIX"},
]


# --------------------------------------------------
# Fetch one index from the existing m.Stock gateway
# --------------------------------------------------

def fetch_index(index):
    query = urlencode({
        "exchange": index["exchange"],
        "symbol": index["symbol"],
    })

    url = f"{GATEWAY_URL}/index-quote?{query}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Financial-OS-Gateway-Secret": MSTOCK_GATEWAY_SECRET,
        },
        method="GET",
    )

    with urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not isinstance(result, dict):
        raise ValueError("Gateway returned an invalid response.")

    # Support the gateway's top-level or nested response format.
    price = result.get("last_price")
    quote = {}
    data = result.get("data", {})
    if isinstance(data, dict):
        candidate = data.get(f'{index["exchange"]}:{index["symbol"]}', {})
        if isinstance(candidate, dict):
            quote = candidate
            if price is None:
                price = quote.get("last_price")

    if result.get("status") not in (None, "success"):
        raise ValueError("Gateway reported an unsuccessful response.")

    if price is None:
        raise ValueError("Index price was not present in the response.")

    try:
        numeric_price = float(price)
    except (TypeError, ValueError) as exc:
        raise ValueError("Index price was not numeric.") from exc
    if not math.isfinite(numeric_price) or numeric_price <= 0:
        raise ValueError("Index price was not a valid positive finite number.")

    raw_previous_close = (quote.get("ohlc") or {}).get("close") if isinstance(quote.get("ohlc"), dict) else None
    try:
        previous_close = float(raw_previous_close) if raw_previous_close not in (None, "") else None
    except (TypeError, ValueError):
        previous_close = None
    if previous_close is not None and (not math.isfinite(previous_close) or previous_close <= 0):
        previous_close = None
    change = numeric_price - previous_close if previous_close is not None else None
    percent_change = (change / previous_close * 100) if previous_close is not None else None

    return {
        "name": index["name"],
        "exchange": index["exchange"],
        "symbol": index["symbol"],
        "last_price": numeric_price,
        "previous_close": previous_close,
        "change": change,
        "percent_change": percent_change,
        "status": "success",
    }


# --------------------------------------------------
# Market Indices API endpoint
# --------------------------------------------------

@router.get("/")
def get_market_indices():
    if not GATEWAY_URL:
        raise HTTPException(status_code=503, detail="Market data gateway is not configured.")
    indices = []
    errors = []

    for index in SUPPORTED_INDICES:
        try:
            indices.append(fetch_index(index))

        except (HTTPError, URLError, TimeoutError, ValueError,
                json.JSONDecodeError, OSError) as exc:
            errors.append({
                "name": index["name"],
                "message": str(exc),
            })

    if not indices:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve market indices.",
                "errors": errors,
            },
        )

    return {
        "engine": "Market Indices Engine",
        "version": "1.0",
        "status": "success" if not errors else "partial",
        "read_only": True,
        "database_write": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "indices": indices,
        "errors": errors,
    }
