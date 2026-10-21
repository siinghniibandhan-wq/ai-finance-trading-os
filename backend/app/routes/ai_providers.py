"""Authenticated API endpoints for the multi-provider AI gateway."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.routes.auth import get_current_user
from app.services.ai_provider_manager import AIProviderError, generate, provider_status

router = APIRouter(prefix="/api/ai/providers", tags=["AI Providers"])


class ProviderChatRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=40)
    message: str = Field(..., min_length=1, max_length=8000)


@router.get("/status", dependencies=[Depends(get_current_user)])
def list_provider_status():
    """Return provider readiness without exposing credentials."""
    return {"providers": provider_status()}


@router.post("/chat", dependencies=[Depends(get_current_user)])
def provider_chat(request: ProviderChatRequest):
    """Generate a response using the explicitly selected provider."""
    try:
        return generate(request.provider, request.message)
    except AIProviderError as exc:
        message = str(exc)
        status_code = 503 if "not configured" in message else 502
        raise HTTPException(status_code=status_code, detail=message) from None
