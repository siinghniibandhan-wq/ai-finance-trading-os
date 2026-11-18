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

GATEWAY_URL = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")

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
            "X-Financial-OS-Gateway-Secret": os.getenv("MSTOCK_GATEWAY_SECRET", "").strip(),
        },
        method="GET",
    )

    with urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not isinstance(result, dict):
        raise ValueError("Gateway returned an invalid response.")

    if result.get("status") not in (None, "success"):
        raise ValueError("Gateway reported an unsuccessful response.")

    # The gateway may return a quote directly or inside its data object.
    quote = result if result.get("last_price") is not None else None
    if quote is None:
        data = result.get("data", {})
        if isinstance(data, dict):
            expected_key = f'{index["exchange"]}:{index["symbol"]}'
            quote = data.get(expected_key)
            if not isinstance(quote, dict):
                # Some gateway versions normalize index keys differently.
                # A single-quote payload is unambiguous; never guess among many.
                quote = next(iter(data.values()), None) if len(data) == 1 else None

    if not isinstance(quote, dict):
        raise ValueError("Index quote was not present in the response.")

    def numeric_field(*keys):
        for key in keys:
            value = quote.get(key)
            if value in (None, ""):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                return number
        return None

    numeric_price = numeric_field("last_price", "ltp", "lastPrice")
    if numeric_price is None or numeric_price <= 0:
        raise ValueError("Index price was not a valid positive finite number.")

    return {
        "name": index["name"],
        "exchange": index["exchange"],
        "symbol": index["symbol"],
        "last_price": numeric_price,
        "change": numeric_field("change", "net_change", "netChange"),
        "percent_change": numeric_field("percent_change", "per_change", "change_percent", "pChange"),
        "previous_close": numeric_field("previous_close", "prev_close", "previousClose", "close"),
        "open": numeric_field("open", "open_price"),
        "high": numeric_field("high", "day_high"),
        "low": numeric_field("low", "day_low"),
        "market_timestamp": (
            quote.get("exchange_timestamp")
            or quote.get("exchange_time")
            or quote.get("last_traded_timestamp")
            or quote.get("last_traded_time")
            or quote.get("timestamp")
        ),
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
