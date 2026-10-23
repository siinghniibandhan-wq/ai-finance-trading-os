import json
from unittest.mock import patch

import pytest

from app.services import ai_providers


def test_unknown_provider_is_rejected():
    with pytest.raises(ai_providers.ProviderError, match="Unsupported"):
        ai_providers.generate("not-a-provider", "hello")


def test_missing_gemini_key_is_reported(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch.object(ai_providers, "_get_api_key", return_value=None):
        with pytest.raises(ai_providers.ProviderError, match="not configured"):
            ai_providers.generate("gemini", "hello")


def test_openai_compatible_provider_returns_normalized_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = {"choices": [{"message": {"content": "Budget carefully."}}]}
    with patch.object(ai_providers, "_post_json", return_value=response) as post:
        result = ai_providers.generate("openai", "Help with a budget")
    assert result["status"] == "success"
    assert result["provider"] == "openai"
    assert result["answer"] == "Budget carefully."
    assert post.call_args.args[0] == "https://api.openai.com/v1/chat/completions"
    assert post.call_args.args[1]["Authorization"] == "Bearer test-key"


def test_gemini_adapter_normalizes_text_and_ignores_non_text_parts(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    response = {"candidates": [{"content": {"parts": [
        {"text": "Hello"}, {"thought_signature": "opaque-signature"},
        None, {"text": " there"}, {"inlineData": {"data": "ignored"}},
    ]}}]}
    with patch.object(ai_providers, "_post_json", return_value=response):
        result = ai_providers.generate("gemini", "hello")
    assert result["answer"] == "Hello there"
    assert result["model"] == "gemini-3.8-flash"


def test_gemini_status_uses_ssm_key_availability(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch.object(ai_providers, "_get_api_key", return_value="ssm-test-key"):
        statuses = ai_providers.provider_status()
    gemini = next(item for item in statuses if item["id"] == "gemini")
    assert gemini["configured"] is True
    assert gemini["default_model"] == "gemini-3.8-flash"


def test_empty_provider_response_is_rejected(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with patch.object(ai_providers, "_post_json", return_value={"choices": []}):
        with pytest.raises(ai_providers.ProviderError, match="no text"):
            ai_providers.generate("openai", "hello")


def test_provider_status_does_not_return_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-leak")
    with patch.object(ai_providers, "_get_api_key", return_value=None):
        statuses = ai_providers.provider_status()
    assert any(item["id"] == "openai" and item["configured"] for item in statuses)
    assert all("key" not in item and "secret" not in item for item in statuses)
    assert "do-not-leak" not in json.dumps(statuses)


def test_gemini_model_is_encoded_as_a_single_url_segment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    with patch.object(ai_providers, "_post_json", return_value={
        "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
    }) as post:
        ai_providers.generate("gemini", "hello", model="model/name?x=1")
    assert "/models/model%2Fname%3Fx%3D1:generateContent" in post.call_args.args[0]


def test_whitespace_only_model_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with patch.object(ai_providers, "_post_json", return_value={
        "choices": [{"message": {"content": "ok"}}]
    }) as post:
        result = ai_providers.generate("openai", "hello", model="   ")
    assert result["model"] == ai_providers.DEFAULT_MODELS["openai"]
    assert post.call_args.args[2]["model"] == ai_providers.DEFAULT_MODELS["openai"]


def test_claude_default_model_is_current_supported_generation():
    assert ai_providers.DEFAULT_MODELS["claude"] == "claude-haiku-4-5-20251001"
