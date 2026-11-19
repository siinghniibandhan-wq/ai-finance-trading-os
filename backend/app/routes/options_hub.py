"""Read-only REST adapter for the m.Stock gateway's optional-chain endpoints.

The gateway owns provider authentication and broker tokens. This route only
forwards the existing Financial OS shared-secret header server-to-server.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

from app.services.mstock_gateway import MSTOCK_GATEWAY_URL, MSTOCK_GATEWAY_SECRET

router = APIRouter(prefix="/api/options-hub", tags=["Options Hub"])

_ALLOWED_EXCHANGES = {"NSE", "BSE"}


def _gateway_get(
    path: str,
    params: dict[str, str],
    label: str,
    *,
    allow_partial: bool = False,
) -> dict:
    if not MSTOCK_GATEWAY_URL or not MSTOCK_GATEWAY_SECRET:
        raise HTTPException(
            status_code=503,
            detail="The Financial OS market gateway is not configured.",
        )

    query = urlencode(params)
    url = f"{MSTOCK_GATEWAY_URL.rstrip('/')}/{path}?{query}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Financial-OS-Gateway-Secret": MSTOCK_GATEWAY_SECRET,
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(
                status_code=503,
                detail=(
                    "The deployed market gateway does not expose the required "
                    "Options REST endpoint yet."
                ),
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"{label} request failed at the market gateway (HTTP {exc.code}).",
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to reach the market gateway for {label.lower()}.",
        ) from exc
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"The market gateway returned invalid JSON for {label.lower()}.",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=502,
            detail=f"The market gateway returned an invalid {label.lower()} response.",
        )

    accepted_statuses = {"success", "partial"} if allow_partial else {"success"}
    if payload.get("status") not in accepted_statuses:
        message = str(payload.get("message") or f"{label} data is unavailable.")[:240]
        raise HTTPException(status_code=502, detail=message)
    return payload


@router.get("/master")
def get_options_master(
    exchange: str = Query("NSE", min_length=3, max_length=3),
):
    """Return the gateway's cached Script Master option-underlying/expiry list."""
    cleaned_exchange = exchange.strip().upper()
    if cleaned_exchange not in _ALLOWED_EXCHANGES:
        raise HTTPException(status_code=400, detail="exchange must be NSE or BSE.")

    payload = _gateway_get(
        "options/master",
        {"exchange": cleaned_exchange},
        "Options master",
    )
    underlyings = payload.get("underlyings")
    if not isinstance(underlyings, list):
        raise HTTPException(status_code=502, detail="Options master response has no underlying list.")

    return {
        "status": "success",
        "exchange": cleaned_exchange,
        "exchange_segment": payload.get("exchange_segment"),
        "underlyings": underlyings,
        "contract_count": payload.get("contract_count"),
        "retrieved_at": payload.get("retrieved_at"),
        "source": {"provider": "m.Stock", "gateway": "Financial OS m.Stock Gateway"},
        "read_only": True,
        "database_write": False,
    }


@router.get("/chain")
def get_options_chain(
    exchange: str = Query("NSE", min_length=3, max_length=3),
    underlying: str = Query(..., min_length=1, max_length=40),
    expiry: str = Query(..., min_length=8, max_length=10),
):
    """Return actual provider-mapped CE/PE contracts and REST quote coverage."""
    cleaned_exchange = exchange.strip().upper()
    cleaned_underlying = underlying.strip().upper()
    cleaned_expiry = expiry.strip()
    if cleaned_exchange not in _ALLOWED_EXCHANGES:
        raise HTTPException(status_code=400, detail="exchange must be NSE or BSE.")
    if not cleaned_underlying or not cleaned_expiry:
        raise HTTPException(status_code=400, detail="underlying and expiry are required.")

    # The gateway deliberately reports "partial" when at least one LTP batch
    # succeeds but one or more contracts lack quotes. Preserve the valid
    # contracts/LTPs instead of converting the whole chain into HTTP 502.
    payload = _gateway_get(
        "options/chain",
        {
            "exchange": cleaned_exchange,
            "underlying": cleaned_underlying,
            "expiry": cleaned_expiry,
        },
        "Options chain",
        allow_partial=True,
    )
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise HTTPException(status_code=502, detail="Options chain response has no contracts list.")

    return {
        "status": payload.get("status", "success"),
        "exchange": cleaned_exchange,
        "exchange_segment": payload.get("exchange_segment"),
        "underlying": cleaned_underlying,
        "expiry": cleaned_expiry,
        "contracts": contracts,
        "quote_count": payload.get("contract_count", payload.get("quote_count", len(contracts))),
        "quote_coverage": payload.get("quote_coverage", 0),
        "open_interest_available": payload.get("open_interest_available") is True,
        "volume_available": payload.get("volume_available") is True,
        "retrieved_at": payload.get("retrieved_at"),
        "source": {"provider": "m.Stock", "gateway": "Financial OS m.Stock Gateway"},
        "read_only": True,
        "database_write": False,
    }
