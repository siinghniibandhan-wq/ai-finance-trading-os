"""
Financial OS — Market Price Service
-----------------------------------

Provider:
- m.Stock Gateway
- m.Stock handles NSE/BSE market data

This service:
- Receives an investment symbol
- Calls the m.Stock gateway
- Extracts the latest market price
- Returns Decimal price to the investment API

IMPORTANT:
- m.Stock API key is NOT stored here.
- TOTP is NOT stored here.
- Access token is NOT stored here.
- All m.Stock authentication remains inside the m.Stock gateway.
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from threading import Event, Lock
from time import monotonic, perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURATION
# ============================================================

MSTOCK_GATEWAY_URL = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")


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
# symbol -> (monotonic insertion time, Decimal price, gateway retrieval timestamp)
_MARKET_PRICE_CACHE = {}
_MARKET_PRICE_CACHE_LOCK = Lock()
# Coalesce concurrent cache misses for the same symbol without blocking other symbols.
_MARKET_PRICE_INFLIGHT = {}


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

    Both are accepted by the m.Stock gateway.
    """

    cleaned = symbol.strip().upper()

    if not cleaned:
        raise MarketPriceError(
            "Investment symbol is required."
        )

    return cleaned


# ============================================================
# m.STOCK GATEWAY REQUEST
# ============================================================

def _canonical_quote_symbol(symbol: str) -> tuple[str | None, str]:
    """Return exchange and base symbol without the common NSE ``-EQ`` suffix."""
    cleaned = normalize_symbol(symbol)
    exchange = None
    if ":" in cleaned:
        prefix, remainder = cleaned.split(":", 1)
        if prefix in {"NSE", "BSE"}:
            exchange, cleaned = prefix, remainder
    if cleaned.endswith("-EQ"):
        cleaned = cleaned[:-3]
    return exchange, cleaned


def _quote_cache_key(symbol: str) -> str:
    """Canonical cache identity; exchange listings must never share a quote."""
    exchange, base = _canonical_quote_symbol(symbol)
    # Unqualified symbols historically use the gateway's default NSE route.
    # Keep BSE listings separate from NSE aliases.
    exchange = exchange or "NSE"
    return f"{exchange}:{base}"


def _quote_symbols_match(requested: str, returned: str) -> bool:
    requested_exchange, requested_base = _canonical_quote_symbol(requested)
    returned_exchange, returned_base = _canonical_quote_symbol(returned)
    if requested_base != returned_base:
        return False
    # Reject explicit exchange conflicts. An unqualified request may be
    # normalized by the gateway to its default exchange symbol.
    return not (requested_exchange and returned_exchange and requested_exchange != returned_exchange)

def _fetch_gateway_quote_details(symbol: str) -> tuple[Decimal, dict]:
    """
    Fetch latest market price from the m.Stock gateway.
    """

    normalized_symbol = normalize_symbol(symbol)

    # The m.Stock gateway expects exchange-qualified cash-equity symbols in
    # the form NSE:RELIANCE-EQ (rather than NSE:RELIANCE). Preserve an existing
    # suffix and do not modify unqualified symbols or non-equity instruments.
    gateway_symbol = normalized_symbol
    if ":" in normalized_symbol:
        exchange, instrument = normalized_symbol.split(":", 1)
        if (
            exchange in {"NSE", "BSE"}
            and instrument
            and not instrument.endswith(("-EQ", "-BE", "-BZ", "-SM", "-ST", "-A", "-B", "-T"))
            and not any(char in instrument for char in "/^")
        ):
            gateway_symbol = f"{exchange}:{instrument}-EQ"

    params = urlencode({
        "symbol": gateway_symbol,
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
            "X-Financial-OS-Gateway-Secret": os.getenv("MSTOCK_GATEWAY_SECRET", "").strip(),
        },
        method="GET",
    )

    try:

        with urlopen(
            request,
            timeout=8,
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

    if not isinstance(payload, dict):
        raise MarketPriceError(
            "m.Stock market gateway returned an invalid response."
        )

    if payload.get("status") != "success":

        raise MarketPriceError(
            payload.get(
                "message",
                "Market gateway returned an error.",
            )
        )

    gateway_data = payload.get("data")
    if gateway_data is None:
        gateway_data = {}
    if not isinstance(gateway_data, dict):
        raise MarketPriceError(
            "m.Stock market gateway returned invalid quote data."
        )

    # ========================================================
    # FIND QUOTE
    # ========================================================

    raw_quote = None

    # First try the exact symbol returned by gateway.
    response_symbol = payload.get("symbol")

    if response_symbol:
        if not _quote_symbols_match(normalized_symbol, str(response_symbol)):
            raise MarketPriceError(
                f"Gateway returned {response_symbol} while {symbol} was requested."
            )
        raw_quote = gateway_data.get(response_symbol)

        # Some gateway responses key data differently from the top-level symbol.
        # A one-quote fallback is safe only when the top-level symbol was matched.
        if raw_quote is None and len(gateway_data) == 1:
            raw_quote = next(iter(gateway_data.values()), None)
    elif len(gateway_data) == 1:
        # Older gateway responses may omit the symbol field entirely. In that
        # case, a single returned quote is the only unambiguous result.
        raw_quote = next(iter(gateway_data.values()), None)

    if raw_quote is None:
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

        price = Decimal(str(raw_price))

    except (
        InvalidOperation,
        ValueError,
    ) as exc:

        raise MarketPriceError(
            f"Invalid market price returned for {symbol}."
        ) from exc

    # Reject provider values that cannot represent a usable market quote.
    # Decimal accepts NaN and Infinity as valid Decimal objects, so conversion
    # alone is not sufficient validation.
    if not price.is_finite() or price <= 0:
        raise MarketPriceError(
            f"Invalid market price returned for {symbol}."
        )

    return price, raw_quote


def _normalise_quote_details(raw_quote: dict) -> dict:
    """Preserve provider quote fields and expose stable names for the UI."""
    details = dict(raw_quote)
    ohlc = raw_quote.get("ohlc")
    if isinstance(ohlc, dict):
        for key in ("open", "high", "low", "close"):
            if details.get(key) in (None, "") and ohlc.get(key) not in (None, ""):
                details[key] = ohlc[key]
    aliases = {
        "previous_close": ("previous_close", "prev_close", "previousClose", "prevClose", "close"),
        "average_price": ("average_price", "avg_price", "average_traded_price", "averageTradedPrice", "avgPrice"),
        "volume": ("volume", "volume_traded_today", "volumeTradedToday", "total_traded_volume"),
        "last_traded_quantity": ("last_traded_quantity", "last_traded_qty", "lastTradedQty"),
        "total_buy_quantity": ("total_buy_quantity", "total_buy_qty", "totalBuyQty", "buy_quantity"),
        "total_sell_quantity": ("total_sell_quantity", "total_sell_qty", "totalSellQty", "sell_quantity"),
        "upper_circuit_limit": ("upper_circuit_limit", "upper_circuit", "upperCircuit", "upperCircuitLimit"),
        "lower_circuit_limit": ("lower_circuit_limit", "lower_circuit", "lowerCircuit", "lowerCircuitLimit"),
        "year_high": ("year_high", "yearHigh", "52_week_high", "52WeekHigh", "high_52_week", "fifty_two_week_high", "week_52_high"),
        "year_low": ("year_low", "yearLow", "52_week_low", "52WeekLow", "low_52_week", "fifty_two_week_low", "week_52_low"),
        "last_traded_timestamp": ("last_traded_timestamp", "last_traded_time", "lastTradedTimestamp"),
        "exchange_timestamp": ("exchange_timestamp", "exchange_time", "exchangeTimestamp"),
        "market_depth": ("market_depth", "marketDepth", "depth"),
    }
    for canonical, candidates in aliases.items():
        if details.get(canonical) not in (None, ""):
            continue
        for candidate in candidates:
            value = details.get(candidate)
            if value not in (None, ""):
                details[canonical] = value
                break
    return details


_LAST_QUOTE_DETAILS = {}


def _fetch_gateway_quote(symbol: str) -> Decimal:
    price, raw_quote = _fetch_gateway_quote_details(symbol)
    _LAST_QUOTE_DETAILS[normalize_symbol(symbol)] = _normalise_quote_details(raw_quote)
    return price


# ============================================================
# PUBLIC MARKET PRICE FUNCTION
# ============================================================

def get_market_quote(
    symbol: str,
) -> dict:
    """
    Return quote data with the original gateway-retrieval timestamp.

    ``retrieved_at`` records when this backend successfully obtained the quote
    from the gateway. It is deliberately not labelled as the exchange/provider
    market timestamp, which this gateway response does not currently expose.
    """
    if not MSTOCK_GATEWAY_URL:
        raise MarketPriceError("MSTOCK_GATEWAY_URL is not configured.")

    normalized_symbol = normalize_symbol(symbol)
    cache_key = _quote_cache_key(normalized_symbol)
    ttl = MARKET_PRICE_CACHE_TTL_SECONDS

    if ttl <= 0:
        fetch_started = perf_counter()
        _LAST_QUOTE_DETAILS.pop(normalized_symbol, None)
        price = _fetch_gateway_quote(normalized_symbol)
        details = _LAST_QUOTE_DETAILS.pop(normalized_symbol, {})
        return {
            "price": price,
            "details": details,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "cache_hit": False,
            "cache_age_seconds": 0.0,
            "provider_latency_ms": round((perf_counter() - fetch_started) * 1000, 2),
        }

    while True:
        with _MARKET_PRICE_CACHE_LOCK:
            now = monotonic()
            cached = _MARKET_PRICE_CACHE.get(cache_key)
            if cached and now - cached[0] <= ttl:
                return {
                    "price": cached[1],
                    "details": cached[3] if len(cached) > 3 else {},
                    "retrieved_at": cached[2],
                    "cache_hit": True,
                    "cache_age_seconds": round(max(0.0, now - cached[0]), 3),
                    "provider_latency_ms": cached[4] if len(cached) > 4 else None,
                }

            flight = _MARKET_PRICE_INFLIGHT.get(cache_key)
            if flight is None:
                flight = {"event": Event(), "price": None, "details": {}, "retrieved_at": None, "provider_latency_ms": None, "error": None}
                _MARKET_PRICE_INFLIGHT[cache_key] = flight
                is_fetcher = True
            else:
                is_fetcher = False

        if not is_fetcher:
            flight["event"].wait()
            if flight["error"] is not None:
                raise flight["error"]
            return {
                "price": flight["price"],
                "details": flight["details"],
                "retrieved_at": flight["retrieved_at"],
                "cache_hit": True,
                "cache_age_seconds": 0.0,
                "provider_latency_ms": flight["provider_latency_ms"],
            }

        try:
            fetch_started = perf_counter()
            _LAST_QUOTE_DETAILS.pop(normalized_symbol, None)
            price = _fetch_gateway_quote(normalized_symbol)
            provider_latency_ms = round((perf_counter() - fetch_started) * 1000, 2)
            details = _LAST_QUOTE_DETAILS.pop(normalized_symbol, {})
            retrieved_at = datetime.now(timezone.utc).isoformat()

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

                _MARKET_PRICE_CACHE[cache_key] = (
                    monotonic(), price, retrieved_at, details, provider_latency_ms
                )
                flight["price"] = price
                flight["details"] = details
                flight["retrieved_at"] = retrieved_at
                flight["provider_latency_ms"] = provider_latency_ms

            return {
                "price": price,
                "details": details,
                "retrieved_at": retrieved_at,
                "cache_hit": False,
                "cache_age_seconds": 0.0,
                "provider_latency_ms": provider_latency_ms,
            }
        except MarketPriceError as exc:
            flight["error"] = exc
            raise
        except Exception as exc:
            # Ensure all waiters receive a defined failure if the provider
            # client raises an unexpected exception outside normal HTTP errors.
            wrapped = MarketPriceError("Unable to fetch a valid market quote.")
            flight["error"] = wrapped
            raise wrapped from exc
        finally:
            with _MARKET_PRICE_CACHE_LOCK:
                _MARKET_PRICE_INFLIGHT.pop(cache_key, None)
                flight["event"].set()


def get_market_price(symbol: str) -> Decimal:
    """Backward-compatible price-only interface for existing callers."""
    return get_market_quote(symbol)["price"]
