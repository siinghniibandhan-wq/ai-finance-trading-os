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

    monkeypatch.setattr(market_history, "urlopen", unavailable)
    with pytest.raises(HTTPException) as exc:
        call_history("2026-10-01", "2026-10-14")
    assert exc.value.status_code == 502
