import json
from io import BytesIO

import pytest
from fastapi import HTTPException

from app.routes import vibe_trading


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = json.dumps(payload).encode()
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return self.payload


def test_vibe_request_uses_only_configured_vibe_host_and_bearer_key(monkeypatch):
    captured = {}
    monkeypatch.setenv("VIBE_TRADING_BASE_URL", "https://vibe.example.test/")
    monkeypatch.setenv("VIBE_TRADING_API_KEY", "test-secret")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers.get("Authorization")
        captured["timeout"] = timeout
        return FakeResponse({"runs": []})

    monkeypatch.setattr(vibe_trading, "urlopen", fake_urlopen)
    result = vibe_trading._request("/runs", query={"limit": 10})

    assert result == {"runs": []}
    assert captured["url"] == "https://vibe.example.test/runs?limit=10"
    assert captured["authorization"] == "Bearer test-secret"
    assert captured["timeout"] == 20


def test_vibe_request_fails_closed_on_auth_failure(monkeypatch):
    from urllib.error import HTTPError

    monkeypatch.setenv("VIBE_TRADING_BASE_URL", "https://vibe.example.test")
    monkeypatch.setenv("VIBE_TRADING_API_KEY", "bad-secret")

    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, BytesIO(b"{}"))

    monkeypatch.setattr(vibe_trading, "urlopen", fake_urlopen)
    with pytest.raises(HTTPException) as exc:
        vibe_trading._request("/runs")
    assert exc.value.status_code == 502
    assert "authentication failed" in exc.value.detail.lower()


def test_session_message_uses_upstream_content_contract():
    body = vibe_trading.SessionMessage(content="Research RELIANCE")
    assert body.model_dump() == {"content": "Research RELIANCE"}


def test_live_order_endpoints_are_not_registered_by_this_router():
    paths = {route.path for route in vibe_trading.router.routes}
    assert "/api/playground/vibe/sessions" in paths
    assert "/api/playground/vibe/sessions/{session_id}/messages" in paths
    assert "/api/playground/vibe/swarm/runs" in paths
    assert "/api/playground/vibe/runs/{run_id}" in paths
    assert not any("order" in path.lower() or "broker" in path.lower() for path in paths)



def test_get_session_messages_uses_vibe_proxy_and_limit(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        vibe_trading,
        "_request",
        lambda path, method="GET", payload=None, query=None: captured.update(
            path=path, method=method, query=query
        ) or [{"role": "assistant", "content": "Research result"}],
    )
    result = vibe_trading.get_session_messages("session_123", limit=25, _user=None)
    assert result == [{"role": "assistant", "content": "Research result"}]
    assert captured == {
        "path": "/sessions/session_123/messages",
        "method": "GET",
        "query": {"limit": 25},
    }


def test_session_message_route_rejects_url_injection(monkeypatch):
    monkeypatch.setattr(vibe_trading, "_request", lambda *args, **kwargs: pytest.fail("must not call upstream"))
    with pytest.raises(HTTPException) as exc:
        vibe_trading.get_session_messages("session_123?x=evil", limit=10, _user=None)
    assert exc.value.status_code == 400



def test_get_run_uses_vibe_api(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        vibe_trading,
        "_request",
        lambda path, method="GET", payload=None, query=None: captured.update(
            path=path, method=method
        ) or {"id": "run_123", "status": "completed"},
    )
    result = vibe_trading.get_run("run_123", _user=None)
    assert result == {"id": "run_123", "status": "completed"}
    assert captured == {"path": "/runs/run_123", "method": "GET"}
