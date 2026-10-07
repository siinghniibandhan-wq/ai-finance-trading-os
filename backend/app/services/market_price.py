"""
Market Price Service
--------------------
Provider layer for fetching market prices.

Current provider:
- Alpha Vantage

This file does NOT update the database.
It only fetches and normalizes a market price.

Environment variable required:
    ALPHAVANTAGE_API_KEY
"""

import json
import os
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


class MarketPriceError(Exception):
    """Raised when a market price cannot be fetched."""


def _candidate_symbols(symbol: str) -> list[str]:
    """
    Build safe provider symbol candidates.

    If an exchange suffix is already supplied, use it directly.
    Otherwise try the BSE-style symbol first, then the raw symbol.
    """
    cleaned = symbol.strip().upper()

    if not cleaned:
        raise MarketPriceError("Investment symbol is required.")

    if "." in cleaned or ":" in cleaned:
        return [cleaned]

    return [f"{cleaned}.BSE", cleaned]


def _fetch_alpha_vantage_quote(symbol: str, api_key: str) -> Decimal:
    """Fetch one quote from Alpha Vantage GLOBAL_QUOTE."""
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    }

    url = f"{ALPHA_VANTAGE_URL}?{urlencode(params)}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AI-Finance-Trading-OS/1.0",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise MarketPriceError(
            f"Alpha Vantage HTTP error: {exc.code}"
        ) from exc
    except URLError as exc:
        raise MarketPriceError(
            "Unable to connect to Alpha Vantage."
        ) from exc
    except TimeoutError as exc:
        raise MarketPriceError(
            "Alpha Vantage request timed out."
        ) from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise MarketPriceError(
            "Alpha Vantage returned an invalid response."
        ) from exc

    # Provider-level errors.
    if payload.get("Error Message"):
        raise MarketPriceError(payload["Error Message"])

    if payload.get("Information"):
        raise MarketPriceError(payload["Information"])

    if payload.get("Note"):
        raise MarketPriceError(payload["Note"])

    quote = payload.get("Global Quote") or {}
    raw_price = quote.get("05. price")

    if raw_price in (None, ""):
        raise MarketPriceError(
            f"No market price returned for symbol {symbol}."
        )

    try:
        return Decimal(str(raw_price))
    except (InvalidOperation, ValueError) as exc:
        raise MarketPriceError(
            f"Invalid market price returned for symbol {symbol}."
        ) from exc


def get_market_price(symbol: str) -> Decimal:
    """
    Fetch the latest available market price.

    The API key is read only from the environment.
    No secret is stored in source code.

    Returns:
        Decimal: latest available price.

    Raises:
        MarketPriceError: when configuration or provider lookup fails.
    """
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")

    if not api_key:
        raise MarketPriceError(
            "ALPHAVANTAGE_API_KEY environment variable is not configured."
        )

    last_error = None

    for candidate in _candidate_symbols(symbol):
        try:
            return _fetch_alpha_vantage_quote(candidate, api_key)
        except MarketPriceError as exc:
            last_error = exc

    raise MarketPriceError(
        f"Unable to fetch market price for {symbol}: {last_error}"
    )
  
