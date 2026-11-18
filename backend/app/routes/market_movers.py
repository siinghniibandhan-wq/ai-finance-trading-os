"""
Financial OS — Market Movers Engine v1.0

Purpose:
- Fetch official market gainers and losers.
- Reuse the existing m.Stock Gateway.
- Use m.Stock's dedicated Type A Gainer/Loser API.
- Keep authentication inside the m.Stock gateway.
- Return a clean Financial OS response.
- Read-only.
- No database writes.

Flow:
Client -> Market Movers Engine -> m.Stock Gateway -> Type A Gainer/Loser API
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from fastapi import APIRouter, HTTPException, Query

from app.services.mstock_gateway import MSTOCK_GATEWAY_URL, MSTOCK_GATEWAY_SECRET


router = APIRouter(
    prefix="/api/market-movers",
    tags=["Market Movers"],
)


def fetch_movers(
    exchange: int,
    security_id_code: int,
    segment: int,
    type_flag: str,
):
    """Forward the Type A gainer/loser form request through the configured Gateway."""
    if not MSTOCK_GATEWAY_URL:
        raise HTTPException(status_code=503, detail="Market data gateway is not configured.")

    payload = urlencode({
        "Exchange": exchange,
        "SecurityIdCode": security_id_code,
        "segment": segment,
        "TypeFlag": type_flag,
    }).encode("utf-8")

    request = Request(
        f"{MSTOCK_GATEWAY_URL}/gainers-losers",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Financial-OS-Gateway-Secret": MSTOCK_GATEWAY_SECRET,
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw_data = response.read().decode("utf-8")
    except HTTPError as exc:
        try:
            error_data = json.loads(exc.read().decode("utf-8"))
        except Exception:
            error_data = {}
        raise HTTPException(
            status_code=502,
            detail=error_data.get("message", "Market movers gateway request failed."),
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach market data gateway.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch market movers.",
        ) from exc

    try:
        payload_data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Market gateway returned invalid JSON.",
        ) from exc

    return payload_data


def extract_type_a_mover_rows(provider_response: dict) -> list:
    """
    Validate the m.Stock Type A response envelope and return its row list.

    Type A success is the JSON boolean true (not the string "success").
    Retain support for the legacy string envelope for backward compatibility.
    """
    if not isinstance(provider_response, dict):
        raise ValueError("Invalid Market Movers provider response")

    status = provider_response.get("status")
    if status is not True and not (
        isinstance(status, str) and status.strip().lower() == "success"
    ):
        message = provider_response.get(
            "message",
            "Market Movers provider request failed",
        )
        raise ValueError(str(message))

    raw_data = provider_response.get("data")
    if raw_data is None:
        raw_data = []
    if not isinstance(raw_data, list):
        raise ValueError("Market Movers provider returned invalid data")

    return raw_data


def normalize_mover(item: dict) -> dict:
    """Map the Type A provider row to the stable Financial OS market-mover shape."""
    return {
        "symbol": item.get("symbol"),
        "name": item.get("symbol_name") or item.get("display_name"),
        "exchange": item.get("exchange"),
        "segment": item.get("segment"),
        "security_id": item.get("security_id"),
        "ltp": item.get("ltp"),
        "change": item.get("change"),
        "percent_change": item.get("per_change"),
        "volume": item.get("volume"),
        "instrument": item.get("instrument"),
        "series": item.get("series"),
        "isin": item.get("isin"),
    }


@router.get("/")
def get_market_movers(
    type: str = Query("gainers", description="gainers or losers"),
    exchange: int = Query(1, description="m.Stock exchange code"),
    security_id_code: int = Query(13, description="m.Stock security ID code"),
    segment: int = Query(1, description="m.Stock market segment code"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of movers"),
):
    mover_type = type.strip().lower()
    if mover_type not in {"gainers", "losers"}:
        raise HTTPException(status_code=400, detail="type must be gainers or losers.")

    type_flag = "G" if mover_type == "gainers" else "L"

    provider_response = fetch_movers(
        exchange=exchange,
        security_id_code=security_id_code,
        segment=segment,
        type_flag=type_flag,
    )

    try:
        raw_data = extract_type_a_mover_rows(provider_response)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    movers = [
        normalize_mover(item)
        for item in raw_data[:limit]
        if isinstance(item, dict)
    ]

    return {
        "status": "success",
        "engine": "Market Movers Engine",
        "version": "1.1",
        "read_only": True,
        "type": mover_type,
        "request": {
            "exchange": exchange,
            "security_id_code": security_id_code,
            "segment": segment,
            "limit": limit,
        },
        "count": len(movers),
        "movers": movers,
        "source": {
            "provider": "m.Stock",
            "gateway": "m.Stock Gateway",
            "endpoint": "/gainers-losers",
        },
        "database_write": False,
        "next_module": "Market Indices Engine",
    }
}
