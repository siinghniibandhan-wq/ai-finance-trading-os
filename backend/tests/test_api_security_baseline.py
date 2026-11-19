"""Security baseline regression tests for the production FastAPI application."""

from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def setup_function():
    main._rate_limit_buckets.clear()


def test_business_and_market_apis_require_a_valid_bearer_session():
    for path in ("/api/accounts/", "/api/market/status", "/api/market-quote/?symbol=RELIANCE", "/api/market-search/?query=RELIANCE"):
        response = client.get(path)
        assert response.status_code == 401, (path, response.status_code, response.text)


def test_auth_login_remains_public_for_sign_in():
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 422


def test_api_rate_limit_returns_429_and_retry_after(monkeypatch):
    monkeypatch.setattr(main, "_RATE_LIMIT_DEFAULT_MAX", 1)
    first = client.get("/api/auth/me")
    second = client.get("/api/accounts/")
    assert first.status_code == 401
    assert second.status_code == 429
    assert int(second.headers["Retry-After"]) >= 1


def test_production_cors_does_not_allow_localhost_origins():
    assert "http://localhost:5173" not in main.CORS_ALLOWED_ORIGINS
    assert "*" not in main.CORS_ALLOWED_ORIGINS


def test_api_responses_include_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_api_documentation_is_disabled_in_production():
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_documentation_requires_explicit_opt_in(monkeypatch):
    from app.api_docs import api_docs_enabled

    monkeypatch.delenv("ENABLE_API_DOCS", raising=False)
    assert api_docs_enabled() is False

    for value in ("1", "true", "yes", "on"):
        monkeypatch.setenv("ENABLE_API_DOCS", value)
        assert api_docs_enabled() is True

    for value in ("0", "false", "no", "off"):
        monkeypatch.setenv("ENABLE_API_DOCS", value)
        assert api_docs_enabled() is False
