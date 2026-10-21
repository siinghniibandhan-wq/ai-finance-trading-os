"""Authenticated AI assistant endpoints for the Finance OS AI module."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.routes.auth import get_current_user
from app.services.ai_providers import ProviderError, generate, provider_status

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    provider: str = Field(default="gemini", max_length=40)
    model: str | None = Field(default=None, max_length=160)


@router.get("/status")
def ai_status():
    providers = provider_status()
    return {
        "module": "AI Assistant",
        "configured": any(item["configured"] for item in providers),
        "providers": providers,
    }


@router.get("/providers", dependencies=[Depends(get_current_user)])
def list_ai_providers():
    """Provider availability and model defaults for the AI module settings UI."""
    return {"providers": provider_status()}


@router.post("/chat", dependencies=[Depends(get_current_user)])
def ai_chat(request: ChatRequest):
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
