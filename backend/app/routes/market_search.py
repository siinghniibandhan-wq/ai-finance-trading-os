"""
Financial OS — Market Search Engine v1.0

Purpose:
- Search the m.Stock instrument master.
- Keep market-search logic separate from market.py.
- Use the existing m.Stock Gateway.
- Read-only.
- No database writes.
- Uses Python standard library only.

Flow:

Client
   ↓
Financial OS Market Search Engine
   ↓
m.Stock Gateway /instruments
   ↓
m.Stock Script Master
"""

import csv
import os
import threading
import time
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query


# ============================================================
# CONFIGURATION
# ============================================================

MSTOCK_GATEWAY_URL = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")

# Cache the gateway's instrument master in this backend process. This is read-only
# and deliberately does not change the search response or ranking behaviour.
try:
    MARKET_INSTRUMENT_CACHE_TTL_SECONDS = max(
        1, int(os.getenv("MARKET_INSTRUMENT_CACHE_TTL_SECONDS", "600"))
    )
except (TypeError, ValueError):
    MARKET_INSTRUMENT_CACHE_TTL_SECONDS = 600

_instrument_master_cache = {"text": None, "loaded_at": 0.0, "parsed_text": None, "fieldnames": None, "rows": None, "stale": False}
_instrument_master_cache_lock = threading.Lock()


def _get_instrument_master_csv():
    """Return the cached instrument-master CSV, refreshing it after the TTL."""
    if not MSTOCK_GATEWAY_URL:
        raise HTTPException(status_code=503, detail="Market data gateway is not configured.")
    now = time.monotonic()
    cached_text = _instrument_master_cache["text"]
    if cached_text is not None and now - _instrument_master_cache["loaded_at"] < MARKET_INSTRUMENT_CACHE_TTL_SECONDS:
        return cached_text

    # Lock and double-check to avoid multiple concurrent refresh downloads.
    with _instrument_master_cache_lock:
        now = time.monotonic()
        cached_text = _instrument_master_cache["text"]
        if cached_text is not None and now - _instrument_master_cache["loaded_at"] < MARKET_INSTRUMENT_CACHE_TTL_SECONDS:
            return cached_text

        gateway_secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
        if not gateway_secret:
            raise HTTPException(
                status_code=503,
                detail="Market gateway authentication is not configured.",
            )

        try:
            request = Request(
                f"{MSTOCK_GATEWAY_URL}/instruments",
                headers={"X-Financial-OS-Gateway-Secret": gateway_secret},
                method="GET",
            )
            with urlopen(request, timeout=8) as response:
                status_code = response.status
                response_text = response.read().decode("utf-8", errors="replace")

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
            # Reject empty or headerless payloads so a transient bad response
            # cannot replace a previously good cache entry.
            reader = csv.DictReader(StringIO(response_text.lstrip("\ufeff")))
            if not reader.fieldnames:
                raise ValueError("Instrument master CSV has no header row.")
            _instrument_master_cache["text"] = response_text
            _instrument_master_cache["loaded_at"] = time.monotonic()
            _instrument_master_cache["stale"] = False
            return response_text
        except HTTPException:
            if cached_text is not None:
                _instrument_master_cache["stale"] = True
                return cached_text
            raise
        except HTTPError as exc:
            if cached_text is not None:
                _instrument_master_cache["stale"] = True
                return cached_text
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
            if cached_text is not None:
                _instrument_master_cache["stale"] = True
                return cached_text
            raise HTTPException(
                status_code=502,
                detail="Unable to reach market data gateway.",
            ) from exc
        except Exception as exc:
            if cached_text is not None:
                _instrument_master_cache["stale"] = True
                return cached_text
            raise HTTPException(
                status_code=502,
                detail="Unable to parse market instrument data.",
            ) from exc


def _classify_listed_product(symbol, name, instrument_type=""):
    """Classify listed NSE/BSE cash instruments for portfolio product-type filters.

    Provider instrument masters do not expose a consistent product-category
    field, so use explicit instrument metadata and common Indian listed-product
    naming patterns. Unknown ordinary cash listings default to stocks.
    """
    symbol_text = str(symbol or "").strip().upper()
    name_text = " " + " ".join(str(name or "").upper().replace("-", " ").split()) + " "
    instrument_text = str(instrument_type or "").strip().upper()

    # Strip common exchange-series suffixes before checking canonical symbols.
    base_symbol = symbol_text
    if "-" in symbol_text:
        prefix, suffix = symbol_text.rsplit("-", 1)
        if suffix in {"EQ", "BE", "BZ", "SM", "ST", "A", "B", "T"}:
            base_symbol = prefix

    known_reit_symbols = {"EMBASSY", "MINDSPACE", "BIRET", "NXST", "NEXUS"}
    if (
        base_symbol in known_reit_symbols
        or " REIT " in name_text
        or " REAL ESTATE TRUST " in name_text
        or " OFFICE PARKS " in name_text
        or " BUSINESS PARKS " in name_text
        or " SELECT TRUST " in name_text
    ):
        return "REITS"

    if (
        instrument_text in {"ETF", "ETN", "EXCHANGE TRADED FUND"}
        or " ETF " in name_text
        or " EXCHANGE TRADED FUND " in name_text
        or " EXCHANGE TRADED " in name_text
        or base_symbol.endswith("BEES")
    ):
        return "ETFS"

    return "STOCKS"


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
    product_type: str = "ALL",
):
    cleaned_query = query.strip().upper()
    cleaned_exchange = exchange.strip().upper()
    if cleaned_exchange not in {"ALL", "NSE", "BSE"}:
        raise HTTPException(status_code=422, detail="Exchange must be ALL, NSE, or BSE.")

    requested_product_type = str(product_type or "ALL").strip().upper().replace(" ", "")
    product_type_aliases = {
        "ALL": "ALL",
        "STOCK": "STOCKS",
        "STOCKS": "STOCKS",
        "ETF": "ETFS",
        "ETFS": "ETFS",
        "REIT": "REITS",
        "REITS": "REITS",
    }
    cleaned_product_type = product_type_aliases.get(requested_product_type)
    if cleaned_product_type is None:
        raise HTTPException(
            status_code=422,
            detail="Product type must be ALL, Stocks, ETFs, or REITs.",
        )

    if not cleaned_query:
        raise HTTPException(
            status_code=400,
            detail="Search query is required.",
        )

    response_text = _get_instrument_master_csv()

    # --------------------------------------------------------
    # Parse Script Master CSV
    # --------------------------------------------------------

    try:
        # Instrument-master exports can use different column labels across
        # gateway versions. Normalize headers once (including a UTF-8 BOM)
        # and map provider aliases into the names used below.
        if _instrument_master_cache.get("parsed_text") == response_text and _instrument_master_cache.get("rows") is not None:
            fieldnames = _instrument_master_cache["fieldnames"]
            raw_rows = _instrument_master_cache["rows"]
        else:
            reader = csv.DictReader(StringIO(response_text.lstrip("\ufeff")))
            if not reader.fieldnames:
                raise ValueError("Instrument master CSV has no header row.")
            fieldnames = list(reader.fieldnames)
            raw_rows = list(reader)
            _instrument_master_cache["parsed_text"] = response_text
            _instrument_master_cache["fieldnames"] = fieldnames
            _instrument_master_cache["rows"] = raw_rows

        def normalize_header(value):
            return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())

        header_lookup = {normalize_header(name): name for name in fieldnames}
        aliases = {
            "exchange": ("exchange", "exch", "exchseg", "exchangesegment", "marketsegment"),
            "tradingsymbol": ("tradingsymbol", "tradingsym", "symbol", "tradingcode", "ticker"),
            "name": ("name", "companyname", "instrumentname", "securityname", "displayname"),
            "instrument_token": ("instrumenttoken", "token", "securityid", "scripcode"),
            "exchange_token": ("exchangetoken", "exchtoken"),
            "last_price": ("lastprice", "ltp", "closeprice", "closingprice"),
            "instrument_type": ("instrumenttype", "type", "series"),
            "segment": ("segment", "exchangesegment", "exchseg"),
            "expiry": ("expiry", "expirydate"),
            "strike": ("strike", "strikeprice"),
            "lot_size": ("lotsize", "marketlotsize"),
        }

        def value_for(row, canonical):
            for alias in aliases.get(canonical, (canonical,)):
                actual = header_lookup.get(normalize_header(alias))
                if actual is not None:
                    value = row.get(actual)
                    if value is not None and str(value).strip() != "":
                        return value
            return None

        results = []

        for raw_row in raw_rows:
            # Canonicalize aliases so downstream result construction remains
            # consistent regardless of the gateway's CSV header spelling.
            row = {key: value_for(raw_row, key) for key in aliases}
            raw_exchange = str(row.get("exchange") or "").strip().upper()
            raw_segment = str(row.get("segment") or "").strip().upper()
            exchange_aliases = {
                "NSECM": "NSE", "NSE_EQ": "NSE", "NSE-EQ": "NSE", "NSE": "NSE",
                "BSECM": "BSE", "BSE_EQ": "BSE", "BSE-EQ": "BSE", "BSE": "BSE",
            }
            # Do not collapse derivatives/currency segments (NSEFO, BSEFO, NSECD, etc.)
            # into cash-equity results. Portfolio search is for listed investment
            # instruments, not futures/options or currency contracts.
            row_exchange = exchange_aliases.get(raw_exchange)
            if row_exchange is None:
                continue
            # m.Stock instrument masters may identify cash equities with
            # segment="EQ" while exchange separately identifies NSE/BSE.
            # Keep the exchange allowlist above as the primary derivatives
            # guard, and accept documented equity-series segment labels here.
            if raw_segment and raw_segment not in {
                "EQ", "BE", "BZ", "SM", "ST", "A", "B", "T",
                "NSECM", "BSECM", "NSE_EQ", "BSE_EQ", "NSE-EQ", "BSE-EQ", "NSE", "BSE",
            }:
                continue
            if not raw_segment and raw_exchange in {"NSEFO", "BSEFO", "NSECD", "BSECD", "NSECOM", "BSECOM"}:
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
            # A cash-equity result must not carry derivative contract fields.
            if expiry or strike:
                continue
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
            classified_product_type = _classify_listed_product(
                symbol,
                name,
                row.get("instrument_type"),
            )
            if cleaned_product_type != "ALL" and classified_product_type != cleaned_product_type:
                continue

            # Group exchange listings for the same security so the NSE/BSE
            # pair stays together instead of showing other company matches
            # between the two listings. The normalized company name is preferred
            # as the cross-exchange identity; the base symbol is the fallback.
            security_key = "".join(ch for ch in name_upper if ch.isalnum()) or base_symbol
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
                "_security_key": security_key,
                "_base_symbol": base_symbol,
            })

        # Rank each security first, then keep its exchange listings adjacent.
        # Exact symbol matches outrank exact company-name matches, then prefixes,
        # then broader partial matches. NSE is the first listing within a pair.
        group_rank = {}
        group_label = {}
        for item in results:
            key = item["_security_key"]
            group_rank[key] = min(group_rank.get(key, item["_rank"]), item["_rank"])
            group_label[key] = min(group_label.get(key, item["_base_symbol"]), item["_base_symbol"])
        results.sort(key=lambda item: (
            group_rank[item["_security_key"]],
            group_label[item["_security_key"]],
            0 if item["exchange"] == "NSE" else 1,
            item["symbol"] or "",
        ))
        results = results[:limit]
        for item in results:
            item.pop("_rank", None)
            item.pop("_security_key", None)
            item.pop("_base_symbol", None)

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
            "gateway": "m.Stock Gateway",
            "endpoint": "/instruments",
            "cache_age_seconds": max(0, int(time.monotonic() - _instrument_master_cache["loaded_at"])),
            "stale": bool(_instrument_master_cache.get("stale")),
            "warning": "Using cached instrument data because gateway refresh failed." if _instrument_master_cache.get("stale") else None,
        },
        "database_write": False,
        "next_module": "Historical Market Data",
    }
