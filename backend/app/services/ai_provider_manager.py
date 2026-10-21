"""Provider-neutral AI gateway for Financial OS.

All credentials are read from backend environment variables. This module does
not persist prompts or credentials and never sends requests to a provider until
a caller explicitly invokes generate().
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AIProviderError(RuntimeError):
    """Safe provider error that must not contain credentials."""


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    model: str
    api_key_env: str | None = None
    protocol: str = "openai"


# Environment variables are deliberately provider-specific. Ollama and local
# OpenAI-compatible servers can work without API keys.
PROVIDERS: dict[str, ProviderConfig] = {
    "gemini": ProviderConfig(
        "Google Gemini",
        "https://generativelanguage.googleapis.com/v1beta",
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "GEMINI_API_KEY",
        "gemini",
    ),
    "claude": ProviderConfig(
        "Anthropic Claude",
        "https://api.anthropic.com/v1",
        os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest"),
        "ANTHROPIC_API_KEY",
        "claude",
    ),
    "openai": ProviderConfig(
        "OpenAI",
        "https://api.openai.com/v1",
        os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "OPENAI_API_KEY",
    ),
    "openrouter": ProviderConfig(
        "OpenRouter",
        "https://openrouter.ai/api/v1",
        os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        "OPENROUTER_API_KEY",
    ),
    "ollama": ProviderConfig(
        "Ollama",
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
        os.getenv("OLLAMA_MODEL", "llama3.2"),
    ),
    "huggingface": ProviderConfig(
        "Hugging Face Inference",
        os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1"),
        os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "HUGGINGFACE_API_KEY",
    ),
    "vllm": ProviderConfig(
        "vLLM",
        os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1"),
        os.getenv("VLLM_MODEL", "default"),
        "VLLM_API_KEY",
    ),
    "lmstudio": ProviderConfig(
        "LM Studio",
        os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"),
        os.getenv("LMSTUDIO_MODEL", "local-model"),
    ),
}


def provider_status() -> list[dict[str, Any]]:
    """Return safe provider metadata; never return API keys or their values."""
    output = []
    for key, config in PROVIDERS.items():
        requires_key = config.api_key_env is not None
        configured = (
            bool(os.getenv(config.api_key_env))
            if config.api_key_env
            else bool(config.base_url)
        )
        output.append({
            "id": key,
            "name": config.name,
            "model": config.model,
            "configured": configured,
            "requires_api_key": requires_key,
        })
    return output


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not return provider response bodies: they may contain sensitive data.
        if exc.code in (401, 403):
            raise AIProviderError("Provider authentication failed; check its backend credential.") from None
        if exc.code == 429:
            raise AIProviderError("Provider rate limit or quota reached.") from None
        raise AIProviderError(f"Provider returned HTTP {exc.code}.") from None
    except (TimeoutError, URLError):
        raise AIProviderError("Provider connection failed or timed out.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise AIProviderError("Provider returned an invalid response.") from None
    return result


def generate(provider: str, message: str) -> dict[str, str]:
    """Generate a text response using one explicitly selected provider."""
    key = provider.strip().lower()
    if key not in PROVIDERS:
        raise AIProviderError("Unsupported AI provider.")
    if not message or not message.strip():
        raise AIProviderError("Message must not be empty.")
    config = PROVIDERS[key]
    api_key = os.getenv(config.api_key_env) if config.api_key_env else None
    if config.api_key_env and not api_key:
        raise AIProviderError(f"{config.name} is not configured; set {config.api_key_env} in the backend environment.")

    system_prompt = (
        "You are an educational assistant in a personal Financial OS. "
        "Do not claim access to accounts or live market data unless explicitly supplied. "
        "Do not guarantee investment returns. Do not present AI output as verified tax "
        "calculations; the deterministic tax engine is authoritative."
    )
    if config.protocol == "gemini":
        url = f"{config.base_url}/models/{config.model}:generateContent?key={api_key}"
        payload = {"systemInstruction": {"parts": [{"text": system_prompt}]},
                   "contents": [{"role": "user", "parts": [{"text": message.strip()}]}]}
        data = _post_json(url, payload, {})
        try:
            answer = "".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"]).strip()
        except (KeyError, IndexError, TypeError):
            answer = ""
    elif config.protocol == "claude":
        data = _post_json(
            f"{config.base_url}/messages",
            {"model": config.model, "max_tokens": 1200, "system": system_prompt,
             "messages": [{"role": "user", "content": message.strip()}]},
            {"x-api-key": api_key or "", "anthropic-version": "2023-06-01"},
        )
        answer = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text").strip()
    else:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        data = _post_json(
            f"{config.base_url.rstrip('/')}/chat/completions",
            {"model": config.model, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.strip()},
            ], "temperature": 0.2},
            headers,
        )
        try:
            answer = data["choices"][0]["message"]["content"]
            if isinstance(answer, list):
                answer = "".join(part.get("text", "") for part in answer if isinstance(part, dict))
            answer = str(answer).strip()
        except (KeyError, IndexError, TypeError):
            answer = ""

    if not answer:
        raise AIProviderError("Provider returned no text.")
    return {"status": "success", "provider": key, "model": config.model, "answer": answer}
