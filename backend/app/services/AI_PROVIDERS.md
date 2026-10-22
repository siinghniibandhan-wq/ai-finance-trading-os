# Finance OS AI module — provider configuration

Configure providers in the **backend deployment environment**, never in frontend .env files or browser storage. Do not commit real keys.

The AI Assistant has a provider selector and a **Test connection** action. The test sends a small prompt to the selected provider, so it may incur provider usage charges.

## Hosted providers

| Provider ID in AI Assistant | Required backend variable | Optional model variable |
|---|---|---|
| Gemini | GEMINI_API_KEY | GEMINI_MODEL |
| Claude | ANTHROPIC_API_KEY | CLAUDE_MODEL |
| OpenAI | OPENAI_API_KEY | OPENAI_MODEL |
| OpenRouter | OPENROUTER_API_KEY | OPENROUTER_MODEL |
| Hugging Face Inference endpoint | HF_TOKEN | HUGGINGFACE_MODEL |

Hugging Face may require HUGGINGFACE_BASE_URL if the selected endpoint is not the default OpenAI-compatible router.

## Additional chat gateway tabs

The AI module also exposes three separate chat tabs, each backed by an OpenAI-compatible endpoint:

| Tab | Backend variables | Notes |
|---|---|---|
| FreeLLMAPI | FREELLMAPI_BASE_URL, FREELLMAPI_API_KEY, optional FREELLMAPI_MODEL | Self-host or configure a trusted FreeLLMAPI endpoint. It is a gateway, not a guarantee of anonymous hosted access. |
| OmniRoute | OMNIROUTE_BASE_URL, OMNIROUTE_API_KEY, optional OMNIROUTE_MODEL | Run/configure OmniRoute and connect its OpenAI-compatible API. Provider accounts, quotas and terms still apply. |
| G0DM0D3 | GODMODE_BASE_URL, GODMODE_API_KEY, optional GODMODE_MODEL | Requires a configured G0DM0D3 API server. Its API may require upstream OpenRouter credentials depending on deployment. |

These tabs are chat-only. Project-specific UI features that are not exposed through the configured API are not automatically available inside Financial OS. The G0DM0D3 source is AGPL-3.0; this integration uses an API adapter rather than copying its source UI or server. Review its license and any service terms before self-hosting or distributing modifications.

## Local / OpenAI-compatible endpoints

| Provider ID | Backend variables | Default endpoint |
|---|---|---|
| Ollama | OLLAMA_BASE_URL (or OLLAMA_HOST) | http://localhost:11434/v1 |
| vLLM | VLLM_BASE_URL | http://localhost:8000/v1 |
| LM Studio | LMSTUDIO_BASE_URL | http://localhost:1234/v1 |
| Custom | CUSTOM_BASE_URL, optional AI_CUSTOM_API_KEY | No default |

Local endpoints must be reachable **from the backend process**, not just from a user's browser. For a remote server/container, localhost refers to that server/container.

The provider selector's model field sends the chosen model name to the provider. Set a provider-specific model environment variable to change its default. Model names and availability vary by account, endpoint, and provider.

## Security notes

- Keep all API keys in backend secret/environment settings.
- Do not add keys to source code, frontend settings, logs, or API responses.
- Restrict network access to local-model endpoints and use TLS/authentication for remote endpoints.
- Provider status means configuration is detected; only Test connection checks a live request.
- Responses are financial education, not verified tax calculations or guaranteed investment outcomes.

## Test

From the backend directory, run:

    python -m pytest tests/test_ai_providers.py -q

These tests mock provider HTTP calls; they do not require live API keys or make billable API requests.
