"""Isolated, authenticated proxy for the Vibe-Trading research API.

Playground traffic uses only this router and VIBE_TRADING_BASE_URL.
No m.Stock routes, provider fallback, or live order submission are exposed here.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/playground/vibe", tags=["Vibe Trading Playground"])
DEFAULT_BASE_URL = "http://127.0.0.1:8899"


def _base_url() -> str:
    return os.getenv("VIBE_TRADING_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")


def _request(path: str, method: str = "GET", payload: dict | None = None, query: dict | None = None):
    base = _base_url()
    if not base.startswith(("https://", "http://")):
        raise HTTPException(status_code=503, detail="Vibe Trading base URL must use HTTP or HTTPS.")
    url = f"{base}{path}"
    if query:
        url += "?" + urlencode({k: v for k, v in query.items() if v is not None})
    headers = {"Accept": "application/json", "User-Agent": "Financial-OS-Vibe-Playground/1.0"}
    api_key = os.getenv("VIBE_TRADING_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "application/json")
            if "text/event-stream" in content_type:
                return raw.decode("utf-8", errors="replace")
            if not raw:
                return {}
            try:
                return json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                raise HTTPException(status_code=502, detail="Vibe Trading returned an invalid JSON response.")
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise HTTPException(status_code=502, detail="Vibe Trading authentication failed. Check VIBE_TRADING_API_KEY and the Vibe Trading server configuration.") from exc
        if exc.code == 404:
            raise HTTPException(status_code=502, detail="The configured Vibe Trading server does not expose the requested API endpoint.") from exc
        raise HTTPException(status_code=502, detail=f"Vibe Trading API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise HTTPException(status_code=503, detail="Unable to connect to Vibe Trading. Check VIBE_TRADING_BASE_URL and server availability.") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Vibe Trading API request timed out.") from exc


class SessionCreate(BaseModel):
    config: dict = Field(default_factory=dict)


class SessionMessage(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    attachments: list[dict] = Field(default_factory=list)


class SwarmRunRequest(BaseModel):
    preset: str | None = None
    prompt: str = Field(min_length=1, max_length=12000)
    config: dict = Field(default_factory=dict)


@router.get("/status")
def status(_user=Depends(get_current_user)):
    configured = bool(os.getenv("VIBE_TRADING_BASE_URL", "").strip())
    return {
        "provider": "Vibe Trading",
        "configured": configured,
        "base_url_configured": configured,
        "api_key_configured": bool(os.getenv("VIBE_TRADING_API_KEY", "").strip()),
        "live_execution_exposed": False,
        "note": "Status reports configuration only; it does not submit trading requests.",
    }


@router.get("/runs")
def list_runs(limit: int = Query(20, ge=1, le=100), _user=Depends(get_current_user)):
    return _request("/runs", query={"limit": limit})


@router.get("/alpha")
def list_alphas(limit: int = Query(50, ge=1, le=200), zoo: str | None = None, theme: str | None = None, universe: str | None = None, _user=Depends(get_current_user)):
    return _request("/alpha/list", query={"limit": limit, "zoo": zoo, "theme": theme, "universe": universe})


@router.get("/swarm/presets")
def swarm_presets(_user=Depends(get_current_user)):
    return _request("/swarm/presets")


@router.post("/sessions")
def create_session(body: SessionCreate, _user=Depends(get_current_user)):
    return _request("/sessions", method="POST", payload={"config": body.config})


@router.post("/sessions/{session_id}/messages")
def send_session_message(session_id: str, body: SessionMessage, _user=Depends(get_current_user)):
    safe_id = session_id.strip()
    if not safe_id or "/" in safe_id or safe_id in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid Vibe Trading session ID.")
    return _request(f"/sessions/{safe_id}/messages", method="POST", payload=body.model_dump())


@router.post("/swarm/runs")
def start_swarm_run(body: SwarmRunRequest, _user=Depends(get_current_user)):
    payload = {"prompt": body.prompt, "config": body.config}
    if body.preset:
        payload["preset"] = body.preset
    return _request("/swarm/runs", method="POST", payload=payload)


@router.get("/alpha/{alpha_id}")
def get_alpha(alpha_id: str, _user=Depends(get_current_user)):
    safe_id = alpha_id.strip()
    if not safe_id or "/" in safe_id or safe_id in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid alpha ID.")
    return _request(f"/alpha/{safe_id}")
