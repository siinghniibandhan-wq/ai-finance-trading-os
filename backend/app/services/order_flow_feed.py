"""Read-only server-side adapter for a normalized derivatives gateway snapshot.

The gateway URL is deliberately separate from the cash-equity quote service.
The gateway owns m.Stock login, token renewal, WebSocket binary decoding and
reconnects; credentials must never be sent to browser clients.
"""
import json
import os
from datetime import datetime, timezone
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
    """Raised when the derivatives gateway is unavailable or invalid."""


def _gateway_url() -> str:
    return os.getenv("MSTOCK_DERIVATIVES_GATEWAY_URL", "").strip().rstrip("/")


def get_order_flow_snapshot(symbol: str | None = None) -> dict:
    base = _gateway_url()
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if not base:
        raise OrderFlowFeedError("Derivatives market-data gateway is not configured.")
    if not secret:
        raise OrderFlowFeedError("Derivatives market-data gateway authentication is not configured.")

    params = {"symbol": symbol.strip().upper()} if symbol else {}
    url = f"{base}/order-flow/snapshot"
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
        raise OrderFlowFeedError(f"Derivatives gateway returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OrderFlowFeedError("Unable to connect to derivatives market-data gateway.") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrderFlowFeedError("Derivatives gateway returned invalid JSON.") from exc

    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise OrderFlowFeedError("Derivatives gateway did not return a successful snapshot.")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise OrderFlowFeedError("Derivatives gateway snapshot is missing its data object.")

    contracts = data.get("futures_contracts", [])
    options = data.get("option_contracts", [])
    if not isinstance(contracts, list) or not isinstance(options, list):
        raise OrderFlowFeedError("Derivatives gateway returned invalid contract collections.")

    try:
        contract_months = aggregate_contract_months(contracts)
        option_oi = aggregate_option_oi(options)
        futures = []
        for contract in contracts:
            item = dict(contract)
            if item.get("oi") is not None and item.get("previous_oi") is not None:
                item["oi_change"] = calculate_oi_change(item["oi"], item["previous_oi"])
            futures.append(item)
        feed = feed_status(data.get("last_tick_at"))
    except (TypeError, ValueError) as exc:
        raise OrderFlowFeedError(f"Derivatives gateway data validation failed: {exc}") from exc

    return {
        "status": "success",
        "source": "m.Stock via Financial OS derivatives gateway",
        "read_only": True,
        "as_of": data.get("last_tick_at"),
        "feed": feed,
        "futures_contracts": futures,
        "contract_months": contract_months,
        "option_oi_by_strike": option_oi,
        "historical_oi_included": False,
        "coverage": data.get("coverage"),
        "stream": data.get("stream"),
    }
