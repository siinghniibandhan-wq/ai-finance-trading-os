"""Read-only NSE institutional flow and corporate-action data adapters.

NSE's public web endpoints are not a versioned API contract. Keep this adapter
isolated, validate every response, cache successful snapshots, and surface the
source date/status so callers never mistake stale data for live data.
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["Market Intelligence"])

NSE_HOME = "https://www.nseindia.com/"
NSE_REPORTS = "https://www.nseindia.com/reports/fii-dii/"
NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_CORPORATE_ACTIONS_URL = "https://www.nseindia.com/api/corporates-corporateActions"
NSE_CORPORATE_ACTIONS_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-actions"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": NSE_REPORTS,
}

_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 900
_CORPORATE_CACHE_TTL_SECONDS = 21600


def _nse_json(url: str) -> object:
    """Fetch JSON through a cookie-aware NSE browser session."""
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    for page in (NSE_HOME, NSE_REPORTS):
        request = Request(page, headers={**_HEADERS, "Accept": "text/html,application/xhtml+xml"})
        with opener.open(request, timeout=12) as response:
            response.read(1024)
    request = Request(url, headers=_HEADERS)
    with opener.open(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"NSE returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8-sig"))


def _rows(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "records", "rows", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _parse_date(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y"):
        try:
            return datetime.strptime(raw.title() if "%b" in fmt else raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _number(value: object) -> float | None:
    if value is None or str(value).strip() in {"", "-", "--", "NA", "N/A"}:
        return None
    try:
        number = float(str(value).replace(",", "").replace("₹", "").strip())
        return number if number == number and abs(number) != float("inf") else None
    except (TypeError, ValueError):
        return None


def parse_institutional_rows(payload: object) -> list[dict]:
    parsed = []
    for row in _rows(payload):
        report_date = _parse_date(row.get("date") or row.get("Date"))
        category = str(row.get("category") or row.get("Category") or "").strip()
        category_key = category.lower()
        if not report_date or not category:
            continue
        if "fii" in category_key or "fpi" in category_key:
            investor_type = "FII/FPI"
        elif "dii" in category_key:
            investor_type = "DII"
        else:
            continue
        buy = _number(row.get("buyValue", row.get("buy_value")))
        sell = _number(row.get("sellValue", row.get("sell_value")))
        net = _number(row.get("netValue", row.get("net_value")))
        if buy is None or sell is None or net is None:
            continue
        # Reject inconsistent provider rows rather than silently repairing them.
        if abs((buy - sell) - net) > 0.02:
            continue
        parsed.append({
            "date": report_date,
            "investor_type": investor_type,
            "category": category,
            "buy_value_crore": buy,
            "sell_value_crore": sell,
            "net_value_crore": net,
        })
    parsed.sort(key=lambda item: (item["date"], item["investor_type"]))
    return parsed


def parse_corporate_action_rows(payload: object, symbol: str) -> list[dict]:
    wanted = symbol.strip().upper()
    parsed = []
    for row in _rows(payload):
        row_symbol = str(row.get("symbol") or row.get("Symbol") or "").strip().upper()
        if row_symbol != wanted:
            continue
        purpose = str(row.get("subject") or row.get("purpose") or row.get("Purpose") or "").strip()
        if not purpose:
            continue
        dividend_amount = None
        if re.search(r"dividend", purpose, re.IGNORECASE):
            match = re.search(r"(?:Rs\.?|INR|₹)\s*([0-9]+(?:\.[0-9]+)?)|\b(Re)\s*([0-9]+(?:\.[0-9]+)?)", purpose, re.IGNORECASE)
            if match:
                dividend_amount = _number(match.group(1) or match.group(3))
        parsed.append({
            "symbol": row_symbol,
            "company": str(row.get("company") or row.get("companyName") or "").strip() or None,
            "series": str(row.get("series") or row.get("Series") or "").strip() or None,
            "purpose": purpose,
            "event_type": (
                "dividend" if "dividend" in purpose.lower()
                else "bonus" if "bonus" in purpose.lower()
                else "split" if "split" in purpose.lower()
                else "buyback" if "buyback" in purpose.lower()
                else "rights" if "right" in purpose.lower()
                else "other"
            ),
            "dividend_per_share": dividend_amount,
            "ex_date": _parse_date(row.get("exDate") or row.get("ex_date") or row.get("exdate")),
            "record_date": _parse_date(row.get("recDate") or row.get("recordDate") or row.get("record_date")),
            "book_closure_start": _parse_date(row.get("bcStartDate") or row.get("bc_start_date")),
            "book_closure_end": _parse_date(row.get("bcEndDate") or row.get("bc_end_date")),
            "face_value": _number(row.get("faceVal") or row.get("face_value")),
        })
    parsed.sort(key=lambda item: (item["ex_date"] or item["record_date"] or "", item["purpose"]), reverse=True)
    return parsed


def _cached(key: str, ttl: int, loader) -> dict:
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < ttl:
            return cached[1]
    payload = loader()
    with _cache_lock:
        _cache[key] = (time.monotonic(), payload)
    return payload


def _load_institutional_flow() -> dict:
    try:
        rows = parse_institutional_rows(_nse_json(NSE_FII_DII_URL))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"NSE institutional-flow source is unavailable: {exc}") from exc
    if not rows:
        raise HTTPException(status_code=502, detail="NSE returned no validated FII/FPI and DII rows.")
    report_date = max(row["date"] for row in rows)
    latest = [row for row in rows if row["date"] == report_date]
    return {
        "status": "success",
        "report_date": report_date,
        "rows": latest,
        "currency_unit": "INR crore",
        "scope": "NSE FII/FPI and DII cash-market activity as returned by NSE's report feed",
        "provisional": True,
        "source": {"name": "NSE India", "url": "https://www.nseindia.com/reports/fii-dii/"},
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
    }


@router.get("/api/institutional-flow/")
def get_institutional_flow():
    return _cached("institutional-flow", _CACHE_TTL_SECONDS, _load_institutional_flow)


def _load_corporate_actions(exchange: str, symbol: str) -> dict:
    if exchange != "NSE":
        return {
            "status": "unavailable",
            "exchange": exchange,
            "symbol": symbol,
            "actions": [],
            "message": "Exchange-specific BSE corporate-action data requires an authorised BSE data feed. NSE records are not substituted for BSE records.",
            "source": {"name": "BSE", "url": "https://marketdata.bseindia.com/"},
            "read_only": True,
        }
    today = date.today()
    params = urlencode({
        "index": "equities",
        "from_date": (today - timedelta(days=730)).strftime("%d-%m-%Y"),
        "to_date": today.strftime("%d-%m-%Y"),
        "symbol": symbol,
    })
    try:
        payload = _nse_json(f"{NSE_CORPORATE_ACTIONS_URL}?{params}")
        actions = parse_corporate_action_rows(payload, symbol)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"NSE corporate-action source is unavailable: {exc}") from exc
    return {
        "status": "success",
        "exchange": exchange,
        "symbol": symbol,
        "actions": actions,
        "source": {"name": "NSE India", "url": f"{NSE_CORPORATE_ACTIONS_PAGE}?symbol={symbol}&tabIndex=equity"},
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
    }


@router.get("/api/corporate-actions/")
def get_corporate_actions(
    symbol: str = Query(..., min_length=1, max_length=30, pattern=r"^[A-Za-z0-9&._-]+$"),
    exchange: str = Query("NSE", pattern="^(NSE|BSE)$"),
):
    clean_symbol = symbol.strip().upper()
    key = f"corporate-actions:{exchange}:{clean_symbol}"
    return _cached(key, _CORPORATE_CACHE_TTL_SECONDS, lambda: _load_corporate_actions(exchange, clean_symbol))
