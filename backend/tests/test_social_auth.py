import time

from app.routes import social_auth


def setup_function():
    import os
    os.environ.setdefault("AUTH_SECRET_KEY", "x" * 48)


def test_state_round_trip_and_tamper_detection():
    state = social_auth._make_state("google", "nonce123")
    payload = social_auth._read_state(state)
    assert payload and payload["p"] == "google" and payload["n"] == "nonce123"
    assert social_auth._read_state(state + "x") is None
    assert social_auth._read_state("not-a-state") is None


def test_expired_state_is_rejected(monkeypatch):
    state = social_auth._make_state("github", "n")
    real_time = time.time
    monkeypatch.setattr(social_auth.time, "time", lambda: real_time() + 3600)
    assert social_auth._read_state(state) is None


def test_provider_is_listed_only_when_both_values_are_set(monkeypatch):
    for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    assert social_auth.social_providers() == {"providers": []}
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    assert social_auth.social_providers() == {"providers": []}
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    assert social_auth.social_providers() == {"providers": [{"id": "google", "label": "Google"}]}


def test_social_routes_are_public_and_never_expose_secrets(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "super-secret-value")
    main._rate_limit_buckets.clear()
    client = TestClient(main.app)
    response = client.get("/api/auth/social/providers")
    assert response.status_code == 200
    assert "super-secret-value" not in response.text
    start = client.get("/api/auth/social/google/start", follow_redirects=False)
    assert start.status_code == 302
    assert start.headers["location"].startswith("https://accounts.google.com/")
    assert "super-secret-value" not in start.headers["location"]
    assert "HttpOnly" in start.headers["set-cookie"]


def test_callback_without_matching_cookie_is_rejected(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    main._rate_limit_buckets.clear()
    client = TestClient(main.app)
    state = social_auth._make_state("google", "abc")
    response = client.get(f"/api/auth/social/google/callback?code=x&state={state}", follow_redirects=False)
    assert response.status_code == 302
    assert "social_error=invalid_state" in response.headers["location"]
