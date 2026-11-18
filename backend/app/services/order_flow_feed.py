"""Read-only adapter from the production m.Stock Market Stream to Order Flow.

The gateway owns m.Stock authentication, the SDK WebSocket and packet decoding.
This service consumes its authenticated raw tick snapshot and joins each token
against the gateway's instrument master. It never guesses instrument identity,
previous OI, or price scaling.
"""
import csv
import json
import os
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.order_flow_data import (
    aggregate_contract_months,
    aggregate_option_oi,
    feed_status,
)


class OrderFlowFeedError(Exception):
    """Raised when the derivatives gateway is unavailable or invalid."""


_CACHE_LOCK = threading.Lock()
_INSTRUMENT_CACHE = {"loaded_at": 0.0, "items": None}


def _gateway_url() -> str:
    """Use the same gateway base URL as the existing Markets integrations."""
    return os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")


def _gateway_secret() -> str:
    return os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()


def _request_json(url: str, secret: str, *, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Accept": "application/json",
        "X-Financial-OS-Gateway-Secret": secret,
        "User-Agent": "Financial-OS/1.0",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise OrderFlowFeedError(
            f"Market-stream gateway returned HTTP {exc.code}."
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OrderFlowFeedError(
            "Unable to connect to the m.Stock market-stream gateway."
        ) from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrderFlowFeedError(
            "Market-stream gateway returned invalid JSON."
        ) from exc
    if not isinstance(payload, dict):
        raise OrderFlowFeedError("Market-stream gateway returned an invalid response.")
    return payload


def _load_instrument_metadata(base: str) -> dict[int, dict]:
    """Load the verified token-to-contract mapping from the existing /instruments CSV."""
    try:
        ttl = max(1, int(os.getenv("MSTOCK_INSTRUMENT_CACHE_TTL_SECONDS", "600")))
    except (TypeError, ValueError):
        ttl = 600

    now = time.monotonic()
    cached = _INSTRUMENT_CACHE["items"]
    if cached is not None and now - _INSTRUMENT_CACHE["loaded_at"] < ttl:
        return cached

    with _CACHE_LOCK:
        now = time.monotonic()
        cached = _INSTRUMENT_CACHE["items"]
        if cached is not None and now - _INSTRUMENT_CACHE["loaded_at"] < ttl:
            return cached

        request = Request(f"{base}/instruments", headers={"Accept": "text/csv"}, method="GET")
        try:
            with urlopen(request, timeout=8) as response:
                csv_text = response.read().decode("utf-8-sig", errors="replace")
        except HTTPError as exc:
            raise OrderFlowFeedError(
                f"Instrument master endpoint returned HTTP {exc.code}."
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise OrderFlowFeedError(
                "Unable to retrieve the m.Stock instrument master."
            ) from exc

        reader = csv.DictReader(StringIO(csv_text))
        if not reader.fieldnames:
            raise OrderFlowFeedError("Instrument master CSV is missing its header.")

        metadata = {}
        for row in reader:
            try:
                token = int(str(row.get("instrument_token") or row.get("token") or "").strip())
            except (TypeError, ValueError):
                continue
            if token <= 0 or token in metadata:
                continue
            segment = str(row.get("segment") or "").strip().upper()
            instrument_type = str(row.get("instrument_type") or "").strip().upper()
            exchange = str(row.get("exchange") or "").strip().upper()
            symbol = str(row.get("name") or "").strip().upper()
            tradingsymbol = str(row.get("tradingsymbol") or "").strip()
            expiry = str(row.get("expiry") or "").strip()
            try:
                lot_size = int(str(row.get("lot_size") or "").strip())
            except (TypeError, ValueError):
                continue
            try:
                datetime.strptime(expiry, "%Y-%m-%d")
            except (TypeError, ValueError):
                continue
            if not symbol or not tradingsymbol or exchange not in {"NFO", "BFO", "CDS"} or lot_size <= 0:
                continue

            if segment in {"FUTIDX", "FUTSTK", "FUTCUR"}:
                kind = "future"
                strike = None
            elif segment in {"OPTIDX", "OPTSTK", "OPTCUR"} and instrument_type in {"CE", "PE"}:
                kind = "option"
                try:
                    strike = float(row.get("strike"))
                except (TypeError, ValueError):
                    continue
                if strike <= 0:
                    continue
            else:
                continue

            metadata[token] = {
                "instrument_token": token,
                "symbol": symbol,
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "segment": segment,
                "instrument_kind": kind,
                "option_type": instrument_type if kind == "option" else None,
                "expiry": expiry,
                "strike": strike,
                "lot_size": lot_size,
            }

        _INSTRUMENT_CACHE.update({"loaded_at": time.monotonic(), "items": metadata})
        return metadata


def _select_subscription_tokens(metadata: dict[int, dict], limit: int = 200) -> list[int]:
    """Select a balanced, bounded derivative universe across segments/underlyings."""
    try:
        configured_limit = int(os.getenv("MSTOCK_MARKET_STREAM_TOKEN_LIMIT", str(limit)))
    except (TypeError, ValueError):
        configured_limit = limit
    if configured_limit < 1 or configured_limit > 200:
        raise OrderFlowFeedError("Market-stream subscription limit must be between 1 and 200.")

    grouped: dict[str, dict[str, list[int]]] = {}
    for token, item in metadata.items():
        segment = str(item.get("segment") or "")
        underlying = str(item.get("symbol") or item.get("tradingsymbol") or token)
        grouped.setdefault(segment, {}).setdefault(underlying, []).append(token)

    states = {}
    for segment, underlyings in grouped.items():
        names = sorted(underlyings)
        states[segment] = {
            "names": names,
            "queues": {name: sorted(underlyings[name]) for name in names},
            "offsets": {name: 0 for name in names},
            "cursor": 0,
        }

    selected = []
    segments = sorted(states)
    while len(selected) < configured_limit:
        progressed = False
        for segment in segments:
            if len(selected) >= configured_limit:
                break
            state = states[segment]
            names = state["names"]
            for step in range(len(names)):
                index = (state["cursor"] + step) % len(names)
                name = names[index]
                offset = state["offsets"][name]
                queue = state["queues"][name]
                if offset < len(queue):
                    selected.append(queue[offset])
                    state["offsets"][name] = offset + 1
                    state["cursor"] = (index + 1) % len(names)
                    progressed = True
                    break
        if not progressed:
            break
    return selected


def _ensure_stream_started(base: str, secret: str, metadata: dict[int, dict]) -> None:
    """Idempotently ensure the production worker subscribes to the derivative universe."""
    tokens = _select_subscription_tokens(metadata)
    if not tokens:
        raise OrderFlowFeedError("Instrument master contains no eligible derivative subscriptions.")
    result = _request_json(
        f"{base}/market-stream/start",
        secret,
        method="POST",
        body={"tokens": tokens, "mode": 3},
    )
    if result.get("status") != "success":
        code = str(result.get("code") or "START_FAILED")
        raise OrderFlowFeedError(f"Market-stream subscription could not be started ({code}).")


def _timestamp_iso(value):
    """Convert SDK/Flask timestamp representations to an ISO-8601 UTC value."""
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
        elif isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                parsed = parsedate_to_datetime(value)
        else:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).isoformat()
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def _numeric_tick_value(tick: dict, field: str):
    value = tick.get(field)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0 or number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _normalise_tick(tick: dict, instrument: dict) -> dict:
    """Join SDK-decoded fields with instrument-master identity; do not rescale."""
    return {
        **instrument,
        "price": _numeric_tick_value(tick, "last_price"),
        "volume": _numeric_tick_value(tick, "volume_traded"),
        "oi": _numeric_tick_value(tick, "oi"),
        "last_traded_quantity": _numeric_tick_value(tick, "last_traded_quantity"),
        "average_traded_price": _numeric_tick_value(tick, "average_traded_price"),
        "exchange_timestamp": _timestamp_iso(tick.get("exchange_timestamp")),
        "received_at": _timestamp_iso(tick.get("received_at")),
        "price_units": "provider_sdk_decoded",
    }


def _stream_last_tick(stream: dict, ticks: list[dict]):
    value = stream.get("last_tick_at")
    if value is None:
        received = [
            tick.get("received_at") for tick in ticks
            if isinstance(tick, dict) and tick.get("received_at") is not None
        ]
        value = max(received) if received else None
    return _timestamp_iso(value)


def _feed_state(stream: dict, last_tick_at: str | None) -> dict:
    feed = feed_status(last_tick_at)
    if last_tick_at is None:
        feed["status"] = "disconnected"
    elif feed["status"] == "stale" or stream.get("stale") is True:
        feed["status"] = "stale"
    elif not (
        stream.get("connected") is True
        and stream.get("stream_verified") is True
    ):
        feed["status"] = "disconnected"
    return feed


def get_order_flow_snapshot(symbol: str | None = None) -> dict:
    base = _gateway_url()
    secret = _gateway_secret()
    if not base:
        raise OrderFlowFeedError("Market gateway is not configured.")
    if not secret:
        raise OrderFlowFeedError("Market gateway authentication is not configured.")

    metadata = _load_instrument_metadata(base)
    _ensure_stream_started(base, secret, metadata)

    payload = _request_json(f"{base}/market-stream/snapshot", secret)
    if payload.get("status") != "success":
        raise OrderFlowFeedError("Gateway did not return a successful market-stream snapshot.")

    ticks = payload.get("ticks")
    stream = payload.get("stream")
    if not isinstance(ticks, list):
        raise OrderFlowFeedError("Gateway returned an invalid tick collection.")
    if not isinstance(stream, dict):
        raise OrderFlowFeedError("Gateway returned an invalid stream status object.")
    if any(not isinstance(tick, dict) for tick in ticks):
        raise OrderFlowFeedError("Gateway tick collection contains invalid entries.")

    requested_symbol = symbol.strip().upper() if symbol else None
    futures = []
    options = []
    unmapped = 0

    for tick in ticks:
        raw_token = tick.get("instrument_token", tick.get("token"))
        try:
            token = int(raw_token)
        except (TypeError, ValueError):
            unmapped += 1
            continue
        instrument = metadata.get(token)
        if instrument is None:
            unmapped += 1
            continue
        if requested_symbol and instrument["symbol"] != requested_symbol:
            continue

        normalized = _normalise_tick(tick, instrument)
        if normalized["instrument_kind"] == "future":
            futures.append(normalized)
        elif normalized["instrument_kind"] == "option":
            options.append(normalized)

    futures.sort(key=lambda item: (item.get("symbol") or "", item.get("expiry") or ""))
    options.sort(key=lambda item: (
        item.get("expiry") or "", item.get("strike") or 0,
        item.get("option_type") or "",
    ))

    # Only ticks carrying a provider OI value contribute to strike-wise OI.
    option_oi = aggregate_option_oi([
        {"strike": item["strike"], "option_type": item["option_type"], "oi": item["oi"]}
        for item in options
        if item.get("strike") is not None and item.get("oi") is not None
    ])
    contract_months = aggregate_contract_months([
        {
            "symbol": item["symbol"],
            "expiry": item["expiry"],
            "volume": item["volume"] if item.get("volume") is not None else 0,
            "oi": item["oi"] if item.get("oi") is not None else 0,
        }
        for item in futures
        if item.get("symbol") and item.get("expiry")
    ])

    last_tick_at = _stream_last_tick(stream, ticks)
    feed = _feed_state(stream, last_tick_at)
    return {
        "status": "success",
        "source": "m.Stock via Financial OS market-stream gateway",
        "read_only": True,
        "as_of": last_tick_at,
        "feed": feed,
        "stream": stream,
        "futures_contracts": futures,
        "contract_months": contract_months,
        "option_contracts": options,
        "option_oi_by_strike": option_oi,
        "coverage": {
            "cached_ticks": len(ticks),
            "mapped_derivative_ticks": len(futures) + len(options),
            "unmapped_ticks": unmapped,
            "futures_contracts": len(futures),
            "option_contracts": len(options),
        },
        "historical_oi_included": False,
        "oi_change_available": False,
    }
