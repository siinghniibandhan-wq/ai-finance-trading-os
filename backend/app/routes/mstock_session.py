"""
Financial OS — m.Stock session connection (administrator only).

The administrator types the current 6-digit authenticator code once. The gateway
exchanges it with m.Stock, keeps the resulting access token until it expires, and
all market-data calls reuse that token. The code itself is never stored, and the
token is never returned to the browser.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.models import User
from app.routes.auth import get_current_admin

router = APIRouter(prefix="/api/mstock/session", tags=["m.Stock Session"])


class MstockSessionRequest(BaseModel):
    totp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


def _gateway_call(path: str, payload: dict | None = None) -> dict:
    base = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=503, detail="MSTOCK_GATEWAY_URL is not configured.")
    request = Request(
        f"{base}{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        method="POST" if payload is not None else "GET",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Financial-OS-Gateway-Secret": os.getenv("MSTOCK_GATEWAY_SECRET", "").strip(),
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("detail")
        except (ValueError, UnicodeDecodeError, AttributeError):
            detail = None
        status = exc.code if exc.code in {400, 503} else 502
        raise HTTPException(status_code=status, detail=detail or "m.Stock gateway rejected the request.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Unable to reach the m.Stock gateway.") from exc


@router.get("")
@router.get("/")
def get_mstock_session(admin: User = Depends(get_current_admin)):
    return _gateway_call("/session")


@router.post("")
@router.post("/")
def connect_mstock_session(body: MstockSessionRequest, admin: User = Depends(get_current_admin)):
    return _gateway_call("/session", {"totp": body.totp})
