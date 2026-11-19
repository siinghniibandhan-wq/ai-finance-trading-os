"""Authenticated read-only options market-data adapter through the existing m.Stock Gateway.

The Gateway resolves derivatives from the provider Script Master and enriches
contracts with the documented batched REST LTP endpoint. This route never
places orders and never exposes broker credentials to the browser.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

from app.services.mstock_gateway import MSTOCK_GATEWAY_URL, MSTOCK_GATEWAY_SECRET

router = APIRouter(prefix="/api/options-chain", tags=["Options Chain"])


def _exchange(exchange: str) -> str:
    cleaned = exchange.strip().upper()
    if cleaned not in {"NSE", "BSE"}:
        raise HTTPException(status_code=422, detail="Exchange must be NSE or BSE.")
    return cleaned


def _gateway_get(path: str, query: dict | None = None) -> dict:
    if not MSTOCK_GATEWAY_URL:
        raise HTTPException(status_code=503, detail="Market data gateway is not configured.")
    suffix = f"?{urlencode(query)}" if query else ""
    request = Request(
        f"{MSTOCK_GATEWAY_URL}/{path.lstrip('/')}{suffix}",
        headers={
            "Accept": "application/json",
            "X-Financial-OS-Gateway-Secret": MSTOCK_GATEWAY_SECRET,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            message = body.get("message", "Options market-data request failed.")
        except Exception:
            message = "Options market-data request failed."
        raise HTTPException(status_code=502, detail=message) from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail="Unable to reach the m.Stock Gateway.") from exc
    except (TimeoutError, ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=502, detail="The m.Stock Gateway returned invalid or timed-out options data.") from exc

    if not isinstance(payload, dict) or payload.get("status") != "success":
        message = payload.get("message", "Options market data is unavailable.") if isinstance(payload, dict) else "Invalid options response."
        raise HTTPException(status_code=502, detail=message)
    return payload


@router.get("/master")
def get_option_chain_master(
    exchange: str = Query("NSE", description="NSE or BSE derivatives exchange"),
):
    """Return available option underlyings and expiries from the broker Script Master."""
    selected_exchange = _exchange(exchange)
    payload = _gateway_get("options/master", {"exchange": selected_exchange})
    return {
        "status": "success",
        "exchange": selected_exchange,
        "provider": payload.get("provider", "m.Stock"),
        "underlyings": payload.get("underlyings") or [],
        "contract_count": payload.get("contract_count", 0),
        "retrieved_at": payload.get("retrieved_at"),
    }


@router.get("/")
def get_option_chain(
    underlying: str = Query(..., min_length=1, max_length=40),
    expiry: str = Query(..., min_length=1, max_length=30),
    exchange: str = Query("NSE", description="NSE or BSE derivatives exchange"),
):
    """Return provider contract metadata and actual REST LTPs for one expiry."""
    selected_exchange = _exchange(exchange)
    clean_underlying = underlying.strip().upper()
    clean_expiry = expiry.strip()
    if not clean_underlying or not clean_expiry:
        raise HTTPException(status_code=422, detail="Underlying and expiry are required.")
    payload = _gateway_get("options/chain", {
        "exchange": selected_exchange,
        "underlying": clean_underlying,
        "expiry": clean_expiry,
    })
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise HTTPException(status_code=502, detail="The Gateway returned no valid option contracts.")
    return {
        **payload,
        "exchange": selected_exchange,
        "read_only": True,
        "database_write": False,
    }
