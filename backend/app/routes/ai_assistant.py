"""Authenticated AI assistant endpoints for the Finance OS AI module."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import User
from app.routes.auth import _check_login_rate_limit, get_current_admin
from app.services.ai_providers import ProviderError, generate, list_models, provider_status

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    provider: str = Field(default="gemini", max_length=40)
    model: str | None = Field(default=None, max_length=160)


@router.get("/status")
def ai_status(current_user: User = Depends(get_current_admin)):
    providers = provider_status()
    return {
        "module": "AI Assistant",
        "configured": any(item["configured"] for item in providers),
        "providers": providers,
    }


@router.get("/providers")
def list_ai_providers(current_user: User = Depends(get_current_admin)):
    """Provider availability and model defaults for the AI module settings UI."""
    return {"providers": provider_status()}


@router.post("/chat")
def ai_chat(request: ChatRequest, current_user: User = Depends(get_current_admin)):
    # Each call costs money on the AI provider key: 30 messages per 10 minutes per user.
    _check_login_rate_limit(f"ai-chat:{current_user.id}", max_attempts=30, window=600)
    try:
        return generate(
            provider=request.provider,
            message=request.message.strip(),
            model=request.model,
        )
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("AI provider request failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="AI request failed. Check backend logs and provider settings.",
        ) from exc



@router.get("/models")
def ai_models(
    provider: str = Query(..., max_length=40),
    current_user: User = Depends(get_current_admin),
):
    _check_login_rate_limit(f"ai-models:{current_user.id}", max_attempts=30, window=600)
    try:
        return list_models(provider)
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
