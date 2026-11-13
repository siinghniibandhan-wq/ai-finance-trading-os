"""Read-only m.Stock Type A option-chain adapter using the documented REST contract.

The provider labels these endpoints as forthcoming in its documentation; calls
are therefore opt-in and surfaced as unavailable on provider errors.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/market-options", tags=["Market Options"])
API_BASE = "https://api.mstock.trade/openapi/typea"


def _auth_headers():
    api_key = os.getenv("MSTOCK_STREAM_API_KEY", "").strip()
    access_token = os.getenv("MSTOCK_STREAM_ACCESS_TOKEN", "").strip()
    if not api_key or not access_token:
        raise HTTPException(status_code=503, detail="m.Stock API credentials are not configured.")
    return {
        "X-Mirae-Version": "1",
        "Authorization": f"token {api_key}:{access_token}",
        "Accept": "application/json",
    }


def _provider_get(path):
    request = Request(f"{API_BASE}/{path}", headers=_auth_headers(), method="GET")
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise HTTPException(status_code=502, detail="m.Stock option-chain authentication or API entitlement failed.") from exc
        raise HTTPException(status_code=502, detail="m.Stock option-chain provider request failed.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise HTTPException(status_code=502, detail="Unable to reach m.Stock option-chain API.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="m.Stock option-chain API returned invalid JSON.") from exc
    if not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
        raise HTTPException(status_code=502, detail="m.Stock option-chain response was unsuccessful or malformed.")
    return payload["data"]


@router.get("/master")
def get_option_chain_master(exchange: int = Query(2, ge=1, le=20)):
    data = _provider_get(f"getoptionchainmaster/{exchange}")
    expiries = data.get("dctExp") or {}
    if not isinstance(expiries, dict):
        raise HTTPException(status_code=502, detail="m.Stock option-chain expiry master is malformed.")
    underlying_groups = {}
    for group in ("FUTIDX", "OPTIDX", "OFSTK"):
        rows = data.get(group) or []
        if not isinstance(rows, list):
            continue
        underlying_groups[group] = rows
    return {
        "status": "success",
        "exchange": exchange,
        "expiries": expiries,
        "underlyings": underlying_groups,
        "source": "m.Stock Type A Option Chain Master",
        "read_only": True,
        "database_write": False,
    }


def _parse_side(rows, key):
    parsed = {}
    if not isinstance(rows, list):
        raise HTTPException(status_code=502, detail=f"m.Stock option-chain {key} side is malformed.")
    for raw in rows:
        if not isinstance(raw, str):
            continue
        parts = raw.split(",")
        if len(parts) < 3:
            continue
        try:
            strike = int(parts[1]) / 100
            oi = int(parts[2])
        except (TypeError, ValueError):
            continue
        if strike <= 0 or oi < 0:
            continue
        parsed.setdefault(strike, {"strike": strike, "call_oi": 0, "put_oi": 0})
        parsed[strike][key] += oi
    return parsed


@router.get("/chain")
def get_option_chain(
    exchange: int = Query(2, ge=1, le=20),
    expiry: int = Query(..., gt=0),
    token: int = Query(..., gt=0),
):
    data = _provider_get(f"GetOptionChain/{exchange}/{expiry}/{token}")
    calls = _parse_side(data.get("call", []), "call_oi")
    puts = _parse_side(data.get("put", []), "put_oi")
    strikes = sorted(set(calls) | set(puts))
    rows = [
        {
            "strike": strike,
            "call_oi": calls.get(strike, {}).get("call_oi", 0),
            "put_oi": puts.get(strike, {}).get("put_oi", 0),
        }
        for strike in strikes
    ]
    contract = data.get("contractModel") if isinstance(data.get("contractModel"), dict) else {}
    return {
        "status": "success",
        "exchange": exchange,
        "expiry": expiry,
        "underlying_token": token,
        "underlying_symbol": contract.get("sym"),
        "spot": data.get("spot"),
        "count": len(rows),
        "options": rows,
        "source": "m.Stock Type A Option Chain",
        "read_only": True,
        "database_write": False,
    }
