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

    # Fallback: use the first quote returned.
    if raw_quote is None and gateway_data:

        raw_quote = next(
            iter(gateway_data.values()),
            None,
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

    return _fetch_gateway_quote(
        symbol
    )
