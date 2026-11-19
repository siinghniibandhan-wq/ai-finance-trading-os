import json
from urllib.error import HTTPError
from io import BytesIO

import pytest
from fastapi import HTTPException

from app.routes import options_chain


class _Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self):
        return json.dumps(self.payload).encode()


def test_option_master_uses_existing_gateway_secret_and_exchange_mapping(monkeypatch):
    calls = []
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_chain, "urlopen", lambda request, timeout: calls.append((request, timeout)) or _Response({
        "status": "success", "data": {"OPTIDX": ["NIFTY,26000,2,3"], "dctExp": {"2": 1790000000}}
    }))
    result = options_chain.get_option_chain_master("NSE")
    request, timeout = calls[0]
    assert request.full_url.endswith("/option-chain-master/2")
    assert request.get_header("X-financial-os-gateway-secret") == "test-secret"
    assert timeout == 35
    assert result["data"]["OPTIDX"][0].startswith("NIFTY")


def test_option_chain_validates_exchange_and_contract_identifiers():
    with pytest.raises(HTTPException) as exc:
        options_chain.get_option_chain_master("CDS")
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        options_chain.get_option_chain(expiry=0, token=22, exchange="NSE")
    assert exc.value.status_code == 422


def test_option_chain_returns_gateway_provider_values_without_recalculation(monkeypatch):
    payload = {
        "status": "success", "contracts": [
            {"side": "CE", "strike": 25000, "open_interest": 1234, "last_price": 125.5}
        ], "quote_coverage": 1, "quote_count": 1
    }
    monkeypatch.setattr(options_chain, "_gateway_get", lambda _path: payload)
    result = options_chain.get_option_chain(expiry=1790000000, token=26000, exchange="NSE")
    assert result["contracts"][0]["last_price"] == 125.5
    assert result["contracts"][0]["open_interest"] == 1234
    assert result["read_only"] is True
