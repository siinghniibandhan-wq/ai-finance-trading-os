"""Multi-provider AI gateway for the Finance OS AI module.

All provider credentials remain server-side. Uses the Python standard library
so provider adapters do not add mandatory SDK dependencies.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote


PROVIDERS = {
    "gemini": {"label": "Google Gemini", "env_key": "GEMINI_API_KEY", "kind": "gemini"},
    "claude": {"label": "Anthropic Claude", "env_key": "ANTHROPIC_API_KEY", "kind": "claude"},
    "openai": {"label": "OpenAI", "env_key": "OPENAI_API_KEY", "kind": "openai"},
    "openrouter": {"label": "OpenRouter", "env_key": "OPENROUTER_API_KEY", "kind": "openai"},
    "ollama": {"label": "Ollama", "env_key": None, "kind": "openai"},
    "huggingface": {"label": "Hugging Face", "env_key": "HF_TOKEN", "kind": "openai"},
    "vllm": {"label": "vLLM", "env_key": None, "kind": "openai"},
    "lmstudio": {"label": "LM Studio", "env_key": None, "kind": "openai"},
    "custom": {"label": "Custom OpenAI-compatible API", "env_key": "AI_CUSTOM_API_KEY", "kind": "openai"},
}

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
    "ollama": "llama3.2",
    "huggingface": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "vllm": "Qwen/Qwen2.5-7B-Instruct",
    "lmstudio": "local-model",
    "custom": "default",
}


class ProviderError(RuntimeError):
    pass


def provider_status():
    result = []
    for key, config in PROVIDERS.items():
        configured = bool(os.getenv(config["env_key"])) if config["env_key"] else True
        if key in {"ollama", "vllm", "lmstudio", "custom"}:
            configured = bool(os.getenv(f"{key.upper()}_BASE_URL")) or (
                key == "ollama" and bool(os.getenv("OLLAMA_HOST"))
            )
        result.append({
            "id": key,
            "name": config["label"],
            "configured": configured,
            "default_model": DEFAULT_MODELS[key],
        })
    return result


def _post_json(url: str, headers: dict, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not expose response bodies that could contain provider or account data.
        raise ProviderError(f"Provider returned HTTP {exc.code}. Check provider settings and backend logs.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError("Provider could not be reached or returned an invalid response.") from exc


def generate(provider: str, message: str, model: str | None = None) -> dict:
    key = provider.strip().lower()
    if key not in PROVIDERS:
        raise ProviderError("Unsupported AI provider.")
    model = (model or "").strip() or os.getenv(f"{key.upper()}_MODEL", "").strip() or DEFAULT_MODELS[key]
    system_prompt = (
        "You are the assistant inside a personal Financial OS. Give clear, cautious "
        "financial education. Do not claim to see account data or live market data unless "
        "it is provided. Explain uncertainty and never guarantee returns. Do not present "
        "your output as verified tax calculations or personalised regulated financial advice."
    )
    config = PROVIDERS[key]
    api_key = os.getenv(config["env_key"]) if config["env_key"] else None
    if config["env_key"] and not api_key:
        raise ProviderError(f"{config['label']} is not configured. Set its API key in the backend environment.")

    if config["kind"] == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
        result = _post_json(url, {"x-goog-api-key": api_key}, {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": message}]}],
        })
        answer = "".join(p.get("text", "") for c in result.get("candidates", []) for p in c.get("content", {}).get("parts", []))
    elif config["kind"] == "claude":
        result = _post_json("https://api.anthropic.com/v1/messages", {
            "x-api-key": api_key or "",
            "anthropic-version": "2023-06-01",
        }, {"model": model, "max_tokens": 1200, "system": system_prompt, "messages": [{"role": "user", "content": message}]})
        answer = "".join(block.get("text", "") for block in result.get("content", []) if block.get("type") == "text")
    else:
        base_url = {
            "openai": "https://api.openai.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "huggingface": os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1"),
            "ollama": (lambda value: value if value.endswith("/v1") else value + "/v1")(os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")),
            "vllm": os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
            "lmstudio": os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            "custom": os.getenv("CUSTOM_BASE_URL", ""),
        }[key].rstrip("/")
        if not base_url:
            raise ProviderError("Set CUSTOM_BASE_URL in the backend environment.")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        result = _post_json(f"{base_url}/chat/completions", headers, {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
            "temperature": 0.3,
        })
        choices = result.get("choices", [])
        answer = choices[0].get("message", {}).get("content", "") if choices else ""

    if not isinstance(answer, str) or not answer.strip():
        raise ProviderError("Provider returned no text.")
    return {"status": "success", "provider": key, "provider_name": config["label"], "model": model, "answer": answer.strip()}
