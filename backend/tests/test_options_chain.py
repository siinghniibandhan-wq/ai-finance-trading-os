import json
from urllib.error import URLError
from urllib.request import Request

import pytest
from fastapi import HTTPException

from app.routes import options_chain


def test_options_chain_master_uses_existing_gateway_secret_and_preserves_payload(monkeypatch):
    captured = {}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps({"status": "success", "data": {"contractModel": [], "spot": {}}}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["secret"] = request.get_header("X-financial-os-gateway-secret")
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_chain, "urlopen", fake_urlopen)

    result = options_chain.get_options_chain_master(exchange_id=1)

    assert captured == {
        "url": "http://127.0.0.1:8000/options-chain/master/1",
        "secret": "test-secret",
        "timeout": 15,
    }
    assert result["data"] == {"contractModel": [], "spot": {}}
    assert result["source"]["gateway_endpoint"] == "/options-chain/master/1"


def test_options_chain_data_encodes_expiry_and_keeps_provider_fields(monkeypatch):
    captured = {}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps({"status": "success", "data": {"call": ["1,2,3"], "put": ["4,5,6"], "future": []}}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return Response()

    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_chain, "urlopen", fake_urlopen)

    result = options_chain.get_options_chain(
        exchange_id=1, expiry="2026-11-26", token=26000
    )

    assert captured["url"] == "http://127.0.0.1:8000/options-chain/1/2026-11-26/26000"
    assert result["data"]["call"] == ["1,2,3"]
    assert result["data"]["put"] == ["4,5,6"]
    assert result["data"]["future"] == []


def test_options_chain_rejects_invalid_exchange_and_token():
    with pytest.raises(HTTPException) as exchange_error:
        options_chain.get_options_chain_master(exchange_id=0)
    assert exchange_error.value.status_code == 400

    with pytest.raises(HTTPException) as token_error:
        options_chain.get_options_chain(exchange_id=1, expiry="2026-11-26", token=0)
    assert token_error.value.status_code == 400


def test_options_chain_gateway_connection_error_is_a_502(monkeypatch):
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_chain, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(URLError("offline")))

    with pytest.raises(HTTPException) as error:
        options_chain.get_options_chain_master(exchange_id=1)
    assert error.value.status_code == 502
