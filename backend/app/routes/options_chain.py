"""Authenticated read-only m.Stock option-chain proxy through the existing Gateway."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

from app.services.mstock_gateway import MSTOCK_GATEWAY_URL, MSTOCK_GATEWAY_SECRET

router = APIRouter(prefix="/api/options-chain", tags=["Options Chain"])


def _exchange_code(exchange: str) -> str:
    cleaned = exchange.strip().upper()
    mapping = {"NSE": "2", "NFO": "2", "BSE": "5", "BFO": "5"}
    if cleaned not in mapping:
        raise HTTPException(status_code=422, detail="Exchange must be NSE or BSE.")
    return mapping[cleaned]


def _gateway_get(path: str) -> dict:
    if not MSTOCK_GATEWAY_URL:
        raise HTTPException(status_code=503, detail="Market data gateway is not configured.")
    request = Request(
        f"{MSTOCK_GATEWAY_URL}/{path.lstrip('/')}",
        headers={
            "Accept": "application/json",
            "X-Financial-OS-Gateway-Secret": MSTOCK_GATEWAY_SECRET,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            message = body.get("message", "Option-chain gateway request failed.")
        except Exception:
            message = "Option-chain gateway request failed."
        raise HTTPException(status_code=502, detail=message) from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail="Unable to reach the m.Stock Gateway.") from exc
    except (TimeoutError, ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=502, detail="The m.Stock Gateway returned an invalid or timed-out response.") from exc

    if not isinstance(payload, dict) or payload.get("status") != "success":
        message = payload.get("message", "Option-chain data is unavailable.") if isinstance(payload, dict) else "Invalid option-chain response."
        raise HTTPException(status_code=502, detail=message)
    return payload


@router.get("/master")
def get_option_chain_master(
    exchange: str = Query("NSE", description="NSE or BSE derivatives exchange"),
):
    """Return provider expiry and contract master data; no browser broker credentials."""
    code = _exchange_code(exchange)
    payload = _gateway_get(f"option-chain-master/{code}")
    return {
        "status": "success",
        "exchange": "NSE" if code == "2" else "BSE",
        "provider": payload.get("provider", "m.Stock"),
        "data": payload.get("data") or {},
    }


@router.get("/")
def get_option_chain(
    expiry: int = Query(..., ge=1),
    token: int = Query(..., ge=1),
    exchange: str = Query("NSE", description="NSE or BSE derivatives exchange"),
):
    """Return the selected underlying's provider option chain and live LTP enrichment."""
    code = _exchange_code(exchange)
    payload = _gateway_get(
        f"option-chain/{code}/{quote(str(expiry), safe='')}/{quote(str(token), safe='')}"
    )
    return {
        **payload,
        "exchange": "NSE" if code == "2" else "BSE",
        "read_only": True,
        "database_write": False,
    }
