import pytest
from fastapi import HTTPException

from app.routes.market_history import get_market_history


def call_history(from_date, to_date):
    return get_market_history(
        symbol="RELIANCE",
        exchange="NSE",
        interval="day",
        from_date=from_date,
        to_date=to_date,
    )


def test_market_history_rejects_invalid_calendar_date_before_gateway_call():
    with pytest.raises(HTTPException) as exc:
        call_history("2026-02-30", "2026-03-01")
    assert exc.value.status_code == 400


def test_market_history_rejects_start_date_after_end_date():
    with pytest.raises(HTTPException) as exc:
        call_history("2026-10-15", "2026-10-14")
    assert exc.value.status_code == 400


def test_market_history_accepts_valid_ordered_dates_and_proceeds_to_gateway(monkeypatch):
    # Valid dates pass validation and then fail at the mocked provider boundary.
    from app.routes import market_history
    from urllib.error import URLError

    def unavailable(*args, **kwargs):
        raise URLError("offline test")

    monkeypatch.setattr(market_history, "MSTOCK_GATEWAY_SECRET", "test-gateway-secret")
    monkeypatch.setattr(market_history, "urlopen", unavailable)
    with pytest.raises(HTTPException) as exc:
        call_history("2026-10-01", "2026-10-14")
    assert exc.value.status_code == 502


def test_market_history_authenticates_both_gateway_requests(monkeypatch):
    import json
    from app.routes import market_history

    monkeypatch.setattr(market_history, "MSTOCK_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setattr(market_history, "MSTOCK_GATEWAY_SECRET", "test-gateway-secret")
    requests = []

    class Response:
        def __init__(self, body):
            self.status = 200
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.body

    def fake_urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith("/instruments"):
            return Response(b"exchange,tradingsymbol,instrument_token,name\\nNSE,RELIANCE,2885,Reliance Industries\\n")
        return Response(json.dumps({"status": "success", "data": {"candles": []}}).encode())

    monkeypatch.setattr(market_history, "urlopen", fake_urlopen)
    result = market_history.get_market_history(
        symbol="RELIANCE", exchange="NSE", interval="day",
        from_date="2026-10-01", to_date="2026-10-02",
    )

    assert result["status"] == "success"
    assert len(requests) == 2
    assert all(
        request.get_header("X-financial-os-gateway-secret") == "test-gateway-secret"
        for request in requests
    )
