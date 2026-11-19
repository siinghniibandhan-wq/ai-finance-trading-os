"""Read-only Type A options-chain REST adapter.

This route deliberately preserves the broker payload. The documented compact
call/put/future rows are not decoded into financial metrics until the live
account response contract has been verified.
"""
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

from app.services.mstock_gateway import MSTOCK_GATEWAY_URL, MSTOCK_GATEWAY_SECRET

router = APIRouter(prefix="/api/options-chain", tags=["Options Chain"])


def _gateway_get(path: str) -> dict:
    if not MSTOCK_GATEWAY_URL:
        raise HTTPException(status_code=503, detail="MSTOCK_GATEWAY_URL is not configured.")

    request = Request(
        f"{MSTOCK_GATEWAY_URL}{path}",
        headers={
            "Accept": "application/json",
            "X-Financial-OS-Gateway-Secret": MSTOCK_GATEWAY_SECRET,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 401:
            raise HTTPException(status_code=502, detail="m.Stock Gateway authentication required.") from exc
        if exc.code == 403:
            raise HTTPException(status_code=502, detail="m.Stock Gateway shared-secret validation failed.") from exc
        raise HTTPException(status_code=502, detail=f"Options-chain Gateway request failed (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail="Unable to reach the m.Stock Gateway.") from exc
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=502, detail="Invalid or timed-out options-chain Gateway response.") from exc

    if not isinstance(payload, dict) or payload.get("status") != "success":
        message = payload.get("message") if isinstance(payload, dict) else None
        raise HTTPException(status_code=502, detail=message or "Options-chain Gateway returned an invalid response.")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Options-chain Gateway response did not contain an object payload.")

    return {
        "status": "success",
        "read_only": True,
        "provider": "m.Stock",
        "data": data,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": {"gateway": "m.Stock Gateway", "gateway_endpoint": path},
        "data_contract": "raw_provider_payload",
    }


@router.get("/master")
def get_options_chain_master(
    exchange_id: int = Query(1, ge=1, le=99, description="m.Stock Type A exchange identifier"),
):
    if exchange_id < 1:
        raise HTTPException(status_code=400, detail="exchange_id must be positive.")
    return _gateway_get(f"/options-chain/master/{exchange_id}")


@router.get("/")
def get_options_chain(
    exchange_id: int = Query(1, ge=1, le=99),
    expiry: str = Query(..., min_length=8, max_length=20),
    token: int = Query(..., ge=1),
):
    if exchange_id < 1 or token < 1:
        raise HTTPException(status_code=400, detail="exchange_id and token must be positive.")
    if not all(character.isalnum() or character in "-_" for character in expiry):
        raise HTTPException(status_code=400, detail="Invalid expiry value.")
    return _gateway_get(
        f"/options-chain/{exchange_id}/{quote(expiry, safe='-_')}/{token}"
    )
