from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.routes import trading_control


def test_gateway_url_rejects_public_ip(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://54.153.201.74:8000")
    with pytest.raises(HTTPException) as exc:
        trading_control._gateway_base_url()
    assert exc.value.status_code == 503


def test_toggle_requires_gateway_secret(monkeypatch):
    monkeypatch.delenv("MSTOCK_GATEWAY_SECRET", raising=False)
    with pytest.raises(HTTPException) as exc:
        trading_control._gateway_request("/trading-toggle", "POST", {"enabled": True})
    assert exc.value.status_code == 503


def test_toggle_sends_secret_header_only_to_loopback(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "test-secret")
    captured = {}

    class FakeResponse:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b'{"trading_enabled": true, "max_order_value": 10000, "max_order_qty": 10}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["secret"] = request.get_header("X-financial-os-gateway-secret")
        captured["timeout"] = timeout
        return FakeResponse()

    with patch("app.routes.trading_control.urlopen", fake_urlopen):
        result = trading_control._gateway_request("/trading-toggle", "POST", {"enabled": True})

    assert captured["url"] == "http://127.0.0.1:8000/trading-toggle"
    assert captured["secret"] == "test-secret"
    assert result["trading_enabled"] is True
