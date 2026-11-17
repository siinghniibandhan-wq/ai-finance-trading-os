"""Read-only adapter for the existing m.Stock market-stream snapshot.

The gateway owns broker authentication, WebSocket lifecycle and binary decoding.
This adapter never exposes credentials to browser clients and never rescales
prices that the gateway has already decoded.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.services.order_flow_data import (
    aggregate_contract_months,
    aggregate_option_oi,
    calculate_oi_change,
    feed_status,
)


class OrderFlowFeedError(Exception):
    """Raised when the market-stream gateway is unavailable or invalid."""


def _gateway_url() -> str:
    configured = os.getenv("MSTOCK_DERIVATIVES_GATEWAY_URL", "").strip()
    fallback = os.getenv("MSTOCK_GATEWAY_URL", "").strip()
    return (configured or fallback).rstrip("/")


def _tick_timestamp(tick: dict):
    return tick.get("exchange_timestamp") or tick.get("timestamp") or tick.get("last_tick_at")


def _normalize_ticks(ticks: list) -> tuple[list, list, list]:
    """Normalize only ticks carrying explicit instrument-master metadata.

    Token-only ticks are returned separately: token-to-contract identity must
    come from the provider's instrument master, never from guessed token IDs.
    """
    futures, options, unmapped = [], [], []
    for tick in ticks:
        if not isinstance(tick, dict):
            raise ValueError("Each market-stream tick must be an object")
        kind = str(tick.get("instrument_type") or tick.get("segment") or "").strip().upper()
        symbol = str(tick.get("symbol") or tick.get("underlying") or "").strip().upper()
        expiry = str(tick.get("expiry") or "").strip()
        price = tick.get("last_price", tick.get("ltp", tick.get("price")))
        volume = tick.get("volume", tick.get("vol"))
        oi = tick.get("oi", tick.get("open_interest"))
        common = {
            "symbol": symbol,
            "expiry": expiry,
            "price": price,
            "volume": volume,
            "oi": oi,
        }
        if kind.startswith("FUT") and symbol and expiry:
            previous_oi = tick.get("previous_oi", tick.get("prev_oi"))
            if previous_oi is not None:
                common["previous_oi"] = previous_oi
            futures.append(common)
        elif kind.startswith("OPT") and symbol and expiry:
            strike = tick.get("strike", tick.get("strike_price"))
            side = str(tick.get("option_type") or tick.get("right") or "").strip().upper()
            if strike is not None and side in {"CE", "PE"}:
                options.append({
                    "symbol": symbol, "expiry": expiry, "strike": strike,
                    "option_type": side, "oi": oi,
                    "volume": volume, "price": price,
                })
            else:
                unmapped.append(tick)
        else:
            unmapped.append(tick)
    return futures, options, unmapped


def get_order_flow_snapshot(symbol: str | None = None) -> dict:
    base = _gateway_url()
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if not base:
        raise OrderFlowFeedError("Derivatives market-data gateway is not configured.")
    if not secret:
        raise OrderFlowFeedError("Derivatives market-data gateway authentication is not configured.")

    params = {"symbol": symbol.strip().upper()} if symbol else {}
    url = f"{base}/market-stream/snapshot"
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={
        "Accept": "application/json",
        "X-Financial-OS-Gateway-Secret": secret,
        "User-Agent": "Financial-OS/1.0",
    }, method="GET")
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise OrderFlowFeedError(f"Market-stream gateway returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OrderFlowFeedError("Unable to connect to the m.Stock market-stream gateway.") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrderFlowFeedError("Market-stream gateway returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise OrderFlowFeedError("Market-stream gateway returned an invalid snapshot.")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if payload.get("status") not in (None, "success", "ok"):
        raise OrderFlowFeedError("Market-stream gateway did not return a successful snapshot.")
    if not isinstance(data, dict):
        raise OrderFlowFeedError("Market-stream snapshot is missing its data object.")

    # Backward-compatible acceptance of a gateway that already emits the
    # normalized contract envelope; the live gateway currently emits ticks.
    contracts = data.get("futures_contracts")
    options = data.get("option_contracts")
    ticks = data.get("ticks", [])
    if not isinstance(ticks, list):
        raise OrderFlowFeedError("Market-stream gateway returned an invalid ticks collection.")
    try:
        if contracts is None or options is None:
            futures, normalized_options, unmapped = _normalize_ticks(ticks)
            contracts = contracts if contracts is not None else futures
            options = options if options is not None else normalized_options
        else:
            unmapped = []
        if not isinstance(contracts, list) or not isinstance(options, list):
            raise ValueError("contract collections must be lists")
        contract_months = aggregate_contract_months(contracts) if contracts else []
        option_oi = aggregate_option_oi(options) if options else []
        futures = []
        for contract in contracts:
            item = dict(contract)
            if item.get("oi") is not None and item.get("previous_oi") is not None:
                item["oi_change"] = calculate_oi_change(item["oi"], item["previous_oi"])
            futures.append(item)
        tick_times = [_tick_timestamp(t) for t in ticks if isinstance(t, dict) and _tick_timestamp(t)]
        last_tick_at = data.get("last_tick_at") or data.get("last_tick") or (tick_times[-1] if tick_times else None)
        feed = feed_status(last_tick_at)
    except (TypeError, ValueError) as exc:
        raise OrderFlowFeedError(f"Market-stream data validation failed: {exc}") from exc

    return {
        "status": "success",
        "source": "m.Stock via Financial OS market-stream gateway",
        "read_only": True,
        "as_of": feed.get("last_tick_at"),
        "feed": feed,
        "futures_contracts": futures,
        "contract_months": contract_months,
        "option_oi_by_strike": option_oi,
        "raw_ticks": ticks,
        "unmapped_tick_count": len(unmapped),
        "price_scaling": "Gateway-decoded prices; no additional scaling applied",
        "historical_oi_included": False,
    }
