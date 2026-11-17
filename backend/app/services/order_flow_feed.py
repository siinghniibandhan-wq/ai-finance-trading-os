"""Read-only adapter from the deployed m.Stock Type-A stream to Order Flow.

The gateway owns m.Stock authentication and binary decoding. Type-A prices are
already divided by 100 by the gateway decoder; this adapter never rescales them.
Instrument identity is resolved only through the gateway's instrument master.
"""
import csv
import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from io import StringIO
from math import isfinite
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.order_flow_data import (
    aggregate_contract_months,
    aggregate_option_oi,
    calculate_oi_change,
    feed_status,
)


class OrderFlowFeedError(Exception):
    """Raised when the market-stream gateway is unavailable or invalid."""


_INSTRUMENT_CACHE_TTL = 600
_instrument_master_cache = {"csv": None, "loaded_at": 0.0, "rows_by_token": {}}
_instrument_master_cache_lock = threading.Lock()
_TYPE_A_EPOCH = datetime(1980, 1, 1, tzinfo=timezone.utc)


def _gateway_url() -> str:
    return os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")


def _gateway_request(url: str, secret: str, *, timeout: int = 8):
    request = Request(url, headers={
        "Accept": "application/json,text/csv",
        "X-Financial-OS-Gateway-Secret": secret,
        "User-Agent": "Financial-OS/1.0",
    }, method="GET")
    return urlopen(request, timeout=timeout)


def _header_key(value: str) -> str:
    return "".join(char for char in str(value or "").strip().lower() if char.isalnum())


def _load_instrument_master(base: str, secret: str) -> dict:
    """Load token identity from the gateway's existing /instruments CSV."""
    now = time.monotonic()
    cached = _instrument_master_cache
    if cached.get("rows_by_token") and now - cached.get("loaded_at", 0) < _INSTRUMENT_CACHE_TTL:
        return cached["rows_by_token"]

    with _instrument_master_cache_lock:
        now = time.monotonic()
        cached = _instrument_master_cache
        if cached.get("rows_by_token") and now - cached.get("loaded_at", 0) < _INSTRUMENT_CACHE_TTL:
            return cached["rows_by_token"]
        try:
            with _gateway_request(f"{base}/instruments", secret) as response:
                text = response.read().decode("utf-8-sig", errors="replace")
            reader = csv.DictReader(StringIO(text))
            if not reader.fieldnames:
                raise ValueError("Instrument master CSV has no header row")
            columns = {_header_key(name): name for name in reader.fieldnames}

            def get(row, *aliases):
                for alias in aliases:
                    column = columns.get(_header_key(alias))
                    value = row.get(column) if column else None
                    if value is not None and str(value).strip():
                        return str(value).strip()
                return ""

            rows_by_token = {}
            for row in reader:
                token = get(row, "instrument_token", "token", "security_id")
                if token.endswith(".0") and token[:-2].isdigit():
                    token = token[:-2]
                kind = get(row, "instrument_type", "type").upper()
                if not token or not (kind.startswith("FUT") or kind.startswith("OPT")):
                    continue
                tradingsymbol = get(row, "tradingsymbol", "trading_symbol", "symbol").upper()
                underlying = get(row, "name", "underlying", "underlying_symbol").upper()
                expiry = get(row, "expiry", "expiry_date")
                if not tradingsymbol or not underlying or not expiry:
                    continue
                instrument = {
                    "token": token,
                    "symbol": underlying,
                    "tradingsymbol": tradingsymbol,
                    "expiry": expiry,
                    "instrument_type": kind,
                    "strike": get(row, "strike", "strike_price"),
                    "exchange": get(row, "exchange"),
                    "segment": get(row, "segment"),
                }
                if kind.startswith("OPT"):
                    instrument["option_type"] = (
                        "CE" if tradingsymbol.endswith("CE")
                        else "PE" if tradingsymbol.endswith("PE")
                        else ""
                    )
                rows_by_token[token] = instrument
            if not rows_by_token:
                raise ValueError("Instrument master contains no mapped futures/options tokens")
            _instrument_master_cache.update({
                "csv": text,
                "loaded_at": time.monotonic(),
                "rows_by_token": rows_by_token,
            })
            return rows_by_token
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, ValueError) as exc:
            raise OrderFlowFeedError(f"Unable to load m.Stock instrument master: {exc}") from exc


def _exchange_timestamp(value):
    """Type-A exchange timestamps are seconds since 1980-01-01 UTC."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not isfinite(float(value)) or value <= 0:
            return None
        return (_TYPE_A_EPOCH + timedelta(seconds=float(value))).isoformat()
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).isoformat()
    return None


def _positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) and number >= 0 else None


def _normalize_type_a_ticks(ticks: list, rows_by_token: dict, symbol: str | None):
    futures, options, unmapped = [], [], []
    for tick in ticks:
        if not isinstance(tick, dict):
            unmapped.append(tick)
            continue
        token = str(tick.get("token", "")).strip()
        if token.endswith(".0") and token[:-2].isdigit():
            token = token[:-2]
        instrument = rows_by_token.get(token)
        if not instrument:
            unmapped.append(tick)
            continue
        if symbol and instrument["symbol"] != symbol:
            continue

        price = _positive_number(tick.get("last_price"))
        volume = _positive_number(tick.get("volume"))
        oi = _positive_number(tick.get("open_interest"))
        exchange_timestamp = _exchange_timestamp(tick.get("exchange_timestamp"))
        if price is None or price <= 0 or volume is None or oi is None or not exchange_timestamp:
            unmapped.append(tick)
            continue

        common = {
            "symbol": instrument["symbol"],
            "tradingsymbol": instrument["tradingsymbol"],
            "expiry": instrument["expiry"],
            "price": price,
            "volume": volume,
            "oi": oi,
            "instrument_token": token,
            "exchange_timestamp": exchange_timestamp,
            "received_at": tick.get("received_at"),
        }
        if instrument["instrument_type"].startswith("FUT"):
            futures.append(common)
        else:
            strike = _positive_number(instrument.get("strike"))
            side = instrument.get("option_type")
            if strike is None or side not in {"CE", "PE"}:
                unmapped.append(tick)
                continue
            options.append({
                **common,
                "strike": strike,
                "option_type": side,
            })
    return futures, options, unmapped


def _latest_exchange_timestamp(ticks: list):
    timestamps = [
        parsed for tick in ticks if isinstance(tick, dict)
        if (parsed := _exchange_timestamp(tick.get("exchange_timestamp"))) is not None
    ]
    if not timestamps:
        return None
    return max(timestamps)


def _normalize_legacy_snapshot(data: dict):
    """Retain support for the normalized gateway contract during migration."""
    contracts = data.get("futures_contracts", [])
    options = data.get("option_contracts", [])
    if not isinstance(contracts, list) or not isinstance(options, list):
        raise ValueError("invalid contract collections")
    contract_months = aggregate_contract_months(contracts) if contracts else []
    option_oi = aggregate_option_oi(options) if options else []
    futures = []
    for contract in contracts:
        item = dict(contract)
        if item.get("oi") is not None and item.get("previous_oi") is not None:
            item["oi_change"] = calculate_oi_change(item["oi"], item["previous_oi"])
        futures.append(item)
    feed = feed_status(data.get("last_tick_at"))
    return futures, options, contract_months, option_oi, feed, 0


def get_order_flow_snapshot(symbol: str | None = None) -> dict:
    base = _gateway_url()
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if not base:
        raise OrderFlowFeedError("Market-data gateway is not configured.")
    if not secret:
        raise OrderFlowFeedError("Market-data gateway authentication is not configured.")

    cleaned_symbol = symbol.strip().upper() if symbol else None
    try:
        with _gateway_request(f"{base}/market-stream/snapshot", secret) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise OrderFlowFeedError(f"Market-stream gateway returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OrderFlowFeedError("Unable to connect to the m.Stock market-stream gateway.") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrderFlowFeedError("Market-stream gateway returned invalid JSON.") from exc

    if not isinstance(payload, dict) or payload.get("status") not in (None, "success"):
        raise OrderFlowFeedError("Market-stream gateway did not return a successful snapshot.")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        raise OrderFlowFeedError("Market-stream gateway returned an invalid snapshot.")

    ticks = data.get("ticks")
    stream = data.get("stream") if isinstance(data.get("stream"), dict) else {}
    try:
        if ticks is not None:
            if not isinstance(ticks, list):
                raise ValueError("ticks must be a list")
            if ticks:
                rows_by_token = _load_instrument_master(base, secret)
                futures, options, unmapped = _normalize_type_a_ticks(ticks, rows_by_token, cleaned_symbol)
            else:
                futures, options, unmapped = [], [], []
            contract_months = aggregate_contract_months(futures) if futures else []
            option_oi = aggregate_option_oi(options) if options else []
            if cleaned_symbol:
                matched_timestamps = [
                    item["exchange_timestamp"] for item in futures + options
                    if item.get("exchange_timestamp")
                ]
                last_tick_at = max(matched_timestamps) if matched_timestamps else None
            else:
                last_tick_at = _latest_exchange_timestamp(ticks)
            feed = feed_status(last_tick_at)
            if stream.get("connected") is False:
                feed["status"] = "disconnected"
            elif stream.get("stale") is True and feed["status"] == "fresh":
                feed["status"] = "stale"
            feed.update({
                "connected": stream.get("connected"),
                "stale": stream.get("stale"),
                "reconnect_count": stream.get("reconnect_count"),
                "mode": stream.get("mode"),
                "cached_instruments": stream.get("cached_instruments"),
            })
        else:
            futures, options, contract_months, option_oi, feed, _ = _normalize_legacy_snapshot(data)
            unmapped = []
    except (TypeError, ValueError) as exc:
        raise OrderFlowFeedError(f"Market-stream data validation failed: {exc}") from exc

    return {
        "status": "success",
        "source": "m.Stock Type-A market stream via Financial OS gateway",
        "read_only": True,
        "as_of": feed.get("last_tick_at"),
        "feed": feed,
        "futures_contracts": futures,
        "contract_months": contract_months,
        "option_contracts": options,
        "option_oi_by_strike": option_oi,
        "raw_ticks": ticks or [],
        "unmapped_tick_count": len(unmapped),
        "price_scaling": "Type A decoder already applied the 1/100 divisor; no additional scaling",
        "historical_oi_included": False,
    }
