"""Join m.Stock Type A ticks to verified derivative instrument metadata."""
import csv
import json
import math
import os
import threading
import time
from datetime import datetime, timezone
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.order_flow_data import (
    aggregate_contract_months, aggregate_option_oi, feed_status,
)


class OrderFlowFeedError(Exception):
    """Gateway unavailable or returned an invalid market-data payload."""


_master_lock = threading.Lock()
_master_cache = {"loaded_at": 0.0, "rows": None}
_MASTER_TTL_SECONDS = 600


def _gateway_url():
    return (
        os.getenv("MSTOCK_DERIVATIVES_GATEWAY_URL", "").strip()
        or os.getenv("MSTOCK_GATEWAY_URL", "").strip()
    ).rstrip("/")


def _request(url, accept, *, method="GET", body=None):
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if not secret:
        raise OrderFlowFeedError("Market-data gateway authentication is not configured.")
    request = Request(url, headers={
        "Accept": accept,
        "X-Financial-OS-Gateway-Secret": secret,
        "User-Agent": "Financial-OS/1.0",
    }, data=body, method=method)
    try:
        with urlopen(request, timeout=8) as response:
            return response.read()
    except HTTPError as exc:
        raise OrderFlowFeedError(f"Market-data gateway returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OrderFlowFeedError("Unable to connect to the market-data gateway.") from exc


def _key(value):
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def _value(row, *aliases):
    normalized = {_key(k): v for k, v in row.items()}
    for alias in aliases:
        value = normalized.get(_key(alias))
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _instrument_master(base):
    now = time.monotonic()
    if _master_cache["rows"] is not None and now - _master_cache["loaded_at"] < _MASTER_TTL_SECONDS:
        return _master_cache["rows"]
    with _master_lock:
        now = time.monotonic()
        if _master_cache["rows"] is not None and now - _master_cache["loaded_at"] < _MASTER_TTL_SECONDS:
            return _master_cache["rows"]
        raw = _request(f"{base}/instruments", "text/csv")
        try:
            rows = list(csv.DictReader(StringIO(raw.decode("utf-8-sig"))))
        except (UnicodeDecodeError, csv.Error) as exc:
            raise OrderFlowFeedError("m.Stock instrument master is invalid.") from exc
        if not rows:
            raise OrderFlowFeedError("m.Stock instrument master is empty.")
        _master_cache.update({"loaded_at": time.monotonic(), "rows": rows})
        return rows



def _start_stream(base, master_rows, symbol):
    """Ensure the gateway subscribes the selected underlying's derivative tokens."""
    if not symbol:
        return
    wanted = symbol.strip().upper()
    tokens = set()
    for row in master_rows:
        underlying = (_value(row, "underlying", "underlying_symbol", "name") or "").upper()
        kind = (_value(row, "instrument_type", "type") or "").upper()
        expiry = _value(row, "expiry", "expiry_date")
        token = _value(row, "instrument_token", "token", "security_id", "scrip_code")
        if underlying != wanted or not expiry or not token or not ("FUT" in kind or "OPT" in kind):
            continue
        try:
            parsed = int(token)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            tokens.add(parsed)
    if not tokens:
        raise OrderFlowFeedError("No derivative instrument tokens found for " + wanted + ".")
    if len(tokens) > 200:
        raise OrderFlowFeedError(
            wanted + " has " + str(len(tokens)) + " derivative tokens; gateway limit is 200. "
            "Narrow the subscribed expiry/strike set before starting the stream."
        )
    body = json.dumps({"tokens": sorted(tokens), "mode": 3}).encode("utf-8")
    try:
        response = _request(
            base + "/market-stream/start",
            "application/json",
            method="POST",
            body=body,
        )
        payload = json.loads(response.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrderFlowFeedError("Market-stream gateway returned an invalid start response.") from exc
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise OrderFlowFeedError("Market-stream gateway did not confirm derivative subscriptions.")


def _number(value):
    if value is None or str(value).strip() == "":
        raise ValueError("missing numeric market field")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("invalid numeric market field")
    return number


def _received_at(value):
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def normalize_market_stream(master_rows, ticks, symbol=None):
    """Normalize only ticks whose token maps to complete provider metadata.

    Type A frames expose raw LTP, volume and current OI. No price divisor,
    previous OI, expiry, strike, underlying or option side is invented here.
    """
    if not isinstance(master_rows, list) or not isinstance(ticks, list):
        raise ValueError("instrument master and ticks must be lists")
    wanted = symbol.strip().upper() if symbol else None
    by_token = {}
    for row in master_rows:
        token = _value(row, "instrument_token", "token", "security_id", "scrip_code")
        try:
            if token:
                by_token[int(token)] = row
        except (ValueError, TypeError):
            continue

    futures, options, timestamps = [], [], []
    for tick in ticks:
        if not isinstance(tick, dict):
            continue
        try:
            token = int(tick.get("token"))
        except (ValueError, TypeError):
            continue
        meta = by_token.get(token)
        if not meta:
            continue
        underlying = _value(meta, "underlying", "underlying_symbol", "name")
        if not underlying:
            continue
        underlying = underlying.upper()
        if wanted and underlying != wanted:
            continue
        expiry = _value(meta, "expiry", "expiry_date")
        kind = (_value(meta, "instrument_type", "type") or "").upper()
        trading_symbol = (_value(meta, "tradingsymbol", "trading_symbol", "symbol") or "").upper()
        if not expiry or tick.get("open_interest") is None:
            continue
        try:
            oi = _number(tick.get("open_interest"))
        except (TypeError, ValueError):
            continue
        received_at = _received_at(tick.get("received_at"))
        if received_at:
            timestamps.append(received_at)
        common = {
            "symbol": underlying, "expiry": expiry, "instrument_token": token,
            "price_raw": tick.get("ltp_raw"), "oi": oi, "last_tick_at": received_at,
        }
        if "FUT" in kind or trading_symbol.endswith("FUT"):
            try:
                volume = _number(tick.get("volume"))
            except (TypeError, ValueError):
                continue
            futures.append({**common, "volume": volume})
            continue

        side = (_value(meta, "option_type", "right") or "").upper()
        if not side:
            side = "CE" if trading_symbol.endswith("CE") else "PE" if trading_symbol.endswith("PE") else ""
        if side not in {"CE", "PE"}:
            continue
        try:
            strike = _number(_value(meta, "strike", "strike_price"))
        except (TypeError, ValueError):
            continue
        options.append({**common, "strike": strike, "option_type": side})

    return {
        "last_tick_at": max(timestamps) if timestamps else None,
        "futures_contracts": futures,
        "option_contracts": options,
    }


def get_order_flow_snapshot(symbol=None):
    base = _gateway_url()
    if not base:
        raise OrderFlowFeedError("m.Stock gateway URL is not configured.")
    master = _instrument_master(base)
    _start_stream(base, master, symbol)
    try:
        payload = json.loads(_request(f"{base}/market-stream/snapshot", "application/json").decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrderFlowFeedError("Market-stream gateway returned invalid JSON.") from exc
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise OrderFlowFeedError("Market-stream gateway did not return a successful snapshot.")
    ticks = payload.get("ticks")
    if not isinstance(ticks, list):
        raise OrderFlowFeedError("Market-stream gateway returned an invalid tick collection.")
    try:
        data = normalize_market_stream(master, ticks, symbol)
        months = aggregate_contract_months(data["futures_contracts"])
        option_oi = aggregate_option_oi(data["option_contracts"])
        freshness = feed_status(data["last_tick_at"])
    except (TypeError, ValueError) as exc:
        raise OrderFlowFeedError(f"Market-stream data validation failed: {exc}") from exc
    return {
        "status": "success",
        "source": "m.Stock Type A via Financial OS gateway",
        "read_only": True,
        "as_of": data["last_tick_at"],
        "feed": freshness,
        "futures_contracts": data["futures_contracts"],
        "contract_months": months,
        "option_oi_by_strike": option_oi,
        "historical_oi_included": False,
    }
