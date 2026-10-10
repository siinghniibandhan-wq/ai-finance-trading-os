# ============================================================
# FINANCIAL OS - GEMINI AI ASSISTANT
# Keeps the Gemini API key on the backend only.
# ============================================================
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)

@router.get("/status")
def ai_status():
    return {"provider": "Google Gemini", "configured": bool(os.getenv("GEMINI_API_KEY"))}

@router.post("/chat")
def ai_chat(request: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Gemini is not configured. Add GEMINI_API_KEY to backend environment variables.")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-latest"),
            contents=(
                "You are the AI assistant inside a personal Financial OS. Give clear, practical, cautious "+
                "financial education. Do not claim to see the user's accounts or live market data unless "+
                "that data is supplied in the conversation. Explain uncertainty and never guarantee returns.\n\n"+
                "User message: " + request.message.strip()
            ),
        )
        answer = getattr(response, "text", None)
        if not answer:
            raise ValueError("Gemini returned no text.")
        return {"status": "success", "provider": "Google Gemini", "answer": answer}
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Gemini SDK is missing. Install google-genai in backend requirements.") from exc

    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception(
            "Gemini API request failed: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail="Gemini request failed. Check backend logs."
        ) from exc
