import json

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


def test_option_master_uses_existing_gateway_secret_and_returns_provider_underlyings(monkeypatch):
    calls = []
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(options_chain, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_chain, "urlopen", lambda request, timeout: calls.append((request, timeout)) or _Response({
        "status": "success", "provider": "m.Stock",
        "underlyings": [{"symbol": "NIFTY", "expiries": ["2026-11-26"]}],
        "contract_count": 100,
    }))
    result = options_chain.get_option_chain_master("NSE")
    request, timeout = calls[0]
    assert request.full_url.endswith("/options/master?exchange=NSE")
    assert request.get_header("X-financial-os-gateway-secret") == "test-secret"
    assert timeout == 45
    assert result["underlyings"][0]["symbol"] == "NIFTY"


def test_options_validate_exchange_and_required_contract_selection():
    with pytest.raises(HTTPException) as exc:
        options_chain.get_option_chain_master("CDS")
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        options_chain.get_option_chain(underlying="", expiry="2026-11-26", exchange="NSE")
    assert exc.value.status_code == 422


def test_option_chain_returns_gateway_ltp_and_contract_values_without_fabrication(monkeypatch):
    payload = {
        "status": "success", "contracts": [
            {"side": "CE", "strike": 25000, "open_interest": None, "last_price": 125.5}
        ], "quote_coverage": 1, "quote_count": 1, "open_interest_available": False,
    }
    monkeypatch.setattr(options_chain, "_gateway_get", lambda *_args, **_kwargs: payload)
    result = options_chain.get_option_chain(underlying="NIFTY", expiry="2026-11-26", exchange="NSE")
    assert result["contracts"][0]["last_price"] == 125.5
    assert result["contracts"][0]["open_interest"] is None
    assert result["read_only"] is True
