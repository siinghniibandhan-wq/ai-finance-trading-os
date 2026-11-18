import json
from urllib.parse import parse_qs

import pytest
from pydantic import ValidationError

from app.routes import market_broker


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def configure_gateway(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://gateway.example:8000")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-gateway-secret")


def test_broker_authentication_forwards_one_totp_to_the_shared_gateway_session(monkeypatch):
    configure_gateway(monkeypatch)
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        assert request.full_url == "http://gateway.example:8000/auth"
        assert request.get_method() == "POST"
        assert request.get_header("X-financial-os-gateway-secret") == "test-gateway-secret"
        assert parse_qs(request.data.decode("utf-8")) == {"totp": ["123456"]}
        return FakeResponse({"status": "success", "message": "m.Stock authentication successful"})

    monkeypatch.setattr(market_broker, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        market_broker,
        "get_order_flow_snapshot",
        lambda: {"feed": {"status": "disconnected"}, "stream": {"running": True}},
    )

    result = market_broker.authenticate_broker_session("123456")

    assert result["status"] == "success"
    assert result["broker_authenticated"] is True
    assert result["market_stream"]["status"] == "disconnected"
    assert result["market_stream"]["running"] is True
    assert result["market_stream"]["cached_instruments"] == 0
    assert len(requests) == 1


def test_broker_authentication_does_not_report_totp_success_as_stream_success(monkeypatch):
    configure_gateway(monkeypatch)

    def fake_urlopen(request, timeout):
        return FakeResponse({"status": "success"})

    monkeypatch.setattr(market_broker, "urlopen", fake_urlopen)

    def fail_to_start():
        raise market_broker.OrderFlowFeedError("WebSocket provider is not connected")

    monkeypatch.setattr(market_broker, "get_order_flow_snapshot", fail_to_start)

    result = market_broker.authenticate_broker_session("123456")

    assert result["broker_authenticated"] is True
    assert result["market_stream"]["status"] == "unavailable"
    assert "WebSocket provider is not connected" in result["market_stream"]["message"]


def test_broker_authentication_rejects_invalid_totp_before_network_request(monkeypatch):
    configure_gateway(monkeypatch)
    called = False

    def fake_urlopen(request, timeout):
        nonlocal called
        called = True
        raise AssertionError("Invalid TOTP must not reach the gateway")

    monkeypatch.setattr(market_broker, "urlopen", fake_urlopen)

    with pytest.raises(ValidationError):
        market_broker.MStockAuthenticationRequest(totp="12ab")

    assert called is False


def test_broker_session_status_uses_gateway_auth_status_and_shared_secret(monkeypatch):
    configure_gateway(monkeypatch)
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return FakeResponse({
            "status": "success",
            "authenticated": True,
            "expires_in_seconds": 36000,
            "stream": {"running": True, "connected": True, "stale": False},
        })

    monkeypatch.setattr(market_broker, "urlopen", fake_urlopen)

    result = market_broker.get_broker_session_status()

    assert result["authenticated"] is True
    assert result["stream"]["connected"] is True
    assert requests[0].full_url == "http://gateway.example:8000/auth/status"
    assert requests[0].get_header("X-financial-os-gateway-secret") == "test-gateway-secret"


def test_broker_status_fails_closed_when_gateway_secret_is_missing(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://gateway.example:8000")
    monkeypatch.delenv("MSTOCK_GATEWAY_SECRET", raising=False)

    with pytest.raises(market_broker.MarketBrokerError, match="not configured"):
        market_broker.get_broker_session_status()
