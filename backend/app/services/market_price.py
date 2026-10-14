"""
Financial OS — Market Price Service
-----------------------------------

Provider:
- AWS m.Stock Gateway
- m.Stock handles NSE/BSE market data

This service:
- Receives an investment symbol
- Calls the AWS m.Stock gateway
- Extracts the latest market price
- Returns Decimal price to the investment API

IMPORTANT:
- m.Stock API key is NOT stored here.
- TOTP is NOT stored here.
- Access token is NOT stored here.
- All m.Stock authentication remains inside the AWS gateway.
"""

import json
import os
from decimal import Decimal, InvalidOperation
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURATION
# ============================================================

MSTOCK_GATEWAY_URL = os.getenv(
    "MSTOCK_GATEWAY_URL",
    "http://54.153.201.74:8000",
).rstrip("/")


def _read_cache_ttl() -> float:
    """Read the shared quote-cache TTL; zero disables service-level caching."""
    try:
        configured = float(os.getenv("MARKET_PRICE_CACHE_TTL_SECONDS", "1.0"))
    except (TypeError, ValueError):
        configured = 1.0
    if configured != configured:  # NaN
        return 1.0
    return max(0.0, min(configured, 10.0))


MARKET_PRICE_CACHE_TTL_SECONDS = _read_cache_ttl()
MARKET_PRICE_CACHE_MAX_ENTRIES = 1000
# symbol -> (monotonic insertion time, Decimal price)
_MARKET_PRICE_CACHE = {}
_MARKET_PRICE_CACHE_LOCK = Lock()


# ============================================================
# CUSTOM ERROR
# ============================================================

class MarketPriceError(Exception):
    """Raised when a market price cannot be fetched."""


# ============================================================
# SYMBOL NORMALIZATION
# ============================================================

def normalize_symbol(symbol: str) -> str:
    """
    Normalize an investment symbol before sending it
    to the market gateway.

    Examples:

        RELIANCE
        NSE:RELIANCE-EQ

    Both are accepted by the AWS gateway.
    """

    cleaned = symbol.strip().upper()

    if not cleaned:
        raise MarketPriceError(
            "Investment symbol is required."
        )

    return cleaned


# ============================================================
# AWS m.STOCK GATEWAY REQUEST
# ============================================================

def _fetch_gateway_quote(symbol: str) -> Decimal:
    """
    Fetch latest market price from the AWS m.Stock gateway.
    """

    normalized_symbol = normalize_symbol(symbol)

    params = urlencode({
        "symbol": normalized_symbol,
    })

    url = (
        f"{MSTOCK_GATEWAY_URL}/quote"
        f"?{params}"
    )

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Financial-OS/1.0",
        },
        method="GET",
    )

    try:

        with urlopen(
            request,
            timeout=15,
        ) as response:

            payload = json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as exc:

        try:
            error_body = (
                exc.read()
                .decode("utf-8")
            )

            error_payload = json.loads(
                error_body
            )

            message = error_payload.get(
                "message",
                "Market gateway request failed.",
            )

        except Exception:
            message = (
                "Market gateway HTTP error."
            )

        raise MarketPriceError(
            f"Market gateway HTTP {exc.code}: {message}"
        ) from exc

    except URLError as exc:

        raise MarketPriceError(
            "Unable to connect to the m.Stock market gateway."
        ) from exc

    except TimeoutError as exc:

        raise MarketPriceError(
            "m.Stock market gateway request timed out."
        ) from exc

    except (
        ValueError,
        UnicodeDecodeError,
    ) as exc:

        raise MarketPriceError(
            "m.Stock market gateway returned an invalid response."
        ) from exc

    # ========================================================
    # PROVIDER RESPONSE VALIDATION
    # ========================================================

    if payload.get("status") != "success":

        raise MarketPriceError(
            payload.get(
                "message",
                "Market gateway returned an error.",
            )
        )

    gateway_data = payload.get(
        "data"
    ) or {}

    # ========================================================
    # FIND QUOTE
    # ========================================================

    raw_quote = None

    # First try the exact symbol returned by gateway.
    response_symbol = payload.get(
        "symbol"
    )

    if response_symbol:
        raw_quote = gateway_data.get(
            response_symbol
        )

    # A single returned quote can be used when the gateway omits or
    # normalizes its symbol key. Never select the first quote from a
    # multi-symbol payload: that can silently return another instrument's price.
    if raw_quote is None and len(gateway_data) == 1:

        raw_quote = next(
            iter(gateway_data.values()),
            None,
        )

    if raw_quote is None and len(gateway_data) > 1:
        raise MarketPriceError(
            f"Gateway response did not contain an exact quote for {symbol}."
        )

    if not isinstance(
        raw_quote,
        dict,
    ):

        raise MarketPriceError(
            f"No market quote returned for {symbol}."
        )

    raw_price = raw_quote.get(
        "last_price"
    )

    if raw_price in (
        None,
        "",
    ):

        raise MarketPriceError(
            f"No latest market price returned for {symbol}."
        )

    # ========================================================
    # DECIMAL CONVERSION
    # ========================================================

    try:

        return Decimal(
            str(raw_price)
        )

    except (
        InvalidOperation,
        ValueError,
    ) as exc:

        raise MarketPriceError(
            f"Invalid market price returned for {symbol}."
        ) from exc


# ============================================================
# PUBLIC MARKET PRICE FUNCTION
# ============================================================

def get_market_price(
    symbol: str,
) -> Decimal:
    """
    Return the latest market price.

    The investment API can call this function without
    knowing anything about m.Stock authentication.

    Authentication remains inside the AWS gateway.
    """

    if not MSTOCK_GATEWAY_URL:

        raise MarketPriceError(
            "MSTOCK_GATEWAY_URL is not configured."
        )

    normalized_symbol = normalize_symbol(symbol)
    ttl = MARKET_PRICE_CACHE_TTL_SECONDS
    now = monotonic()

    if ttl > 0:
        with _MARKET_PRICE_CACHE_LOCK:
            cached = _MARKET_PRICE_CACHE.get(normalized_symbol)
            if cached and now - cached[0] <= ttl:
                return cached[1]

    # Do not hold the cache lock during gateway I/O. Different symbols can
    # still fetch concurrently; this cache is shared by all routes in this process.
    price = _fetch_gateway_quote(normalized_symbol)

    if ttl > 0:
        with _MARKET_PRICE_CACHE_LOCK:
            cutoff = monotonic() - ttl
            expired = [
                key for key, value in _MARKET_PRICE_CACHE.items()
                if value[0] < cutoff
            ]
            for key in expired:
                _MARKET_PRICE_CACHE.pop(key, None)

            if len(_MARKET_PRICE_CACHE) >= MARKET_PRICE_CACHE_MAX_ENTRIES:
                oldest_key = min(
                    _MARKET_PRICE_CACHE,
                    key=lambda key: _MARKET_PRICE_CACHE[key][0],
                )
                _MARKET_PRICE_CACHE.pop(oldest_key, None)

            _MARKET_PRICE_CACHE[normalized_symbol] = (monotonic(), price)

    return price
