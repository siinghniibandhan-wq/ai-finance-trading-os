import json
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from app.routes import options_hub


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_options_master_proxies_gateway_rest_contract_without_exposing_secret(monkeypatch):
    requested = {}

    def fake_urlopen(request, timeout):
        requested["url"] = request.full_url
        requested["headers"] = dict(request.header_items())
        requested["timeout"] = timeout
        return FakeResponse({
            "status": "success",
            "exchange": "NSE",
            "underlyings": [{"symbol": "NIFTY", "expiries": ["2026-11-26"]}],
            "contract_count": 120,
        })

    monkeypatch.setattr(options_hub, "MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setattr(options_hub, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_hub, "urlopen", fake_urlopen)

    result = options_hub.get_options_master(exchange="NSE")

    assert urlparse(requested["url"]).path == "/options/master"
    assert parse_qs(urlparse(requested["url"]).query) == {"exchange": ["NSE"]}
    assert requested["headers"]["X-financial-os-gateway-secret"] == "test-secret"
    assert result["underlyings"][0]["symbol"] == "NIFTY"
    assert "test-secret" not in json.dumps(result)


def test_options_chain_proxies_selected_underlying_and_expiry(monkeypatch):
    requested = {}

    def fake_urlopen(request, timeout):
        requested["url"] = request.full_url
        return FakeResponse({
            "status": "success",
            "exchange": "NSE",
            "underlying": "NIFTY",
            "expiry": "2026-11-26",
            "contracts": [
                {"strike": 25000, "side": "CE", "last_price": 120, "open_interest": None},
                {"strike": 25000, "side": "PE", "last_price": 110, "open_interest": None},
            ],
            "quote_count": 2,
            "quote_coverage": 2,
            "open_interest_available": False,
        })

    monkeypatch.setattr(options_hub, "MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setattr(options_hub, "MSTOCK_GATEWAY_SECRET", "test-secret")
    monkeypatch.setattr(options_hub, "urlopen", fake_urlopen)

    result = options_hub.get_options_chain(
        exchange="NSE", underlying="NIFTY", expiry="2026-11-26",
    )

    assert urlparse(requested["url"]).path == "/options/chain"
    assert parse_qs(urlparse(requested["url"]).query) == {
        "exchange": ["NSE"], "underlying": ["NIFTY"], "expiry": ["2026-11-26"],
    }
    assert len(result["contracts"]) == 2
    assert result["open_interest_available"] is False


@pytest.mark.parametrize("exchange", ["", "BFO", "NFO", "NYSE"])
def test_options_master_rejects_unsupported_exchange(exchange):
    with pytest.raises(HTTPException) as exc:
        options_hub.get_options_master(exchange=exchange)
    assert exc.value.status_code == 400


def test_options_chain_requires_underlying_and_expiry():
    with pytest.raises(HTTPException) as exc:
        options_hub.get_options_chain(exchange="NSE", underlying="", expiry="")
    assert exc.value.status_code == 400
