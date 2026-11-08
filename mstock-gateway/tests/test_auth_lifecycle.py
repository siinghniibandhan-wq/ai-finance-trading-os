from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

import main


def test_token_expiry_is_earlier_of_twelve_hours_and_midnight(monkeypatch):
    now = datetime(2026, 11, 8, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    monkeypatch.setattr(main, "_now_ist", lambda: now)

    assert main._local_token_expiry() == datetime(
        2026, 11, 8, 21, 59, tzinfo=ZoneInfo("Asia/Kolkata")
    )


def test_token_expiry_respects_twelve_hour_limit(monkeypatch):
    now = datetime(2026, 11, 8, 1, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    monkeypatch.setattr(main, "_now_ist", lambda: now)

    assert main._local_token_expiry() == now + timedelta(hours=12) - timedelta(seconds=60)


def test_totp_waits_until_next_period_when_near_expiry(monkeypatch):
    calls = []
    monkeypatch.setattr(main.time, "time", lambda: 100.0)  # 20 seconds remain
    monkeypatch.setattr(main.time, "sleep", lambda seconds: calls.append(seconds))
    monkeypatch.setattr(main.pyotp, "TOTP", lambda secret: type(
        "FakeTotp", (), {"now": lambda self: "123456"}
    )())

    assert main._generate_fresh_totp("secret") == "123456"
    assert calls == []


def test_totp_waits_when_fewer_than_five_seconds_remain(monkeypatch):
    calls = []
    monkeypatch.setattr(main.time, "time", lambda: 128.0)  # 2 seconds remain
    monkeypatch.setattr(main.time, "sleep", lambda seconds: calls.append(seconds))
    monkeypatch.setattr(main.pyotp, "TOTP", lambda secret: type(
        "FakeTotp", (), {"now": lambda self: "654321"}
    )())

    assert main._generate_fresh_totp("secret") == "654321"
    assert calls == [3]


def test_login_rejects_provider_error_payload_without_leaking_message(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "api-key")
    monkeypatch.setattr(main, "TOTP_SECRET", "totp-secret")
    monkeypatch.setattr(main, "_generate_fresh_totp", lambda secret, **kwargs: "123456")
    monkeypatch.setattr(main, "_post_totp_session", lambda code: {
        "status": "error",
        "message": "Please enter correct TOTP - private provider detail",
        "data": None,
    })

    with pytest.raises(HTTPException) as error:
        main._login_with_totp()

    assert error.value.status_code == 503
    assert "private provider detail" not in error.value.detail
    assert "TOTP" in error.value.detail


def test_login_requires_access_token_in_success_payload(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "api-key")
    monkeypatch.setattr(main, "TOTP_SECRET", "totp-secret")
    monkeypatch.setattr(main, "_generate_fresh_totp", lambda secret: "123456")
    monkeypatch.setattr(main, "_post_totp_session", lambda code: {
        "status": "success", "data": {"refresh_token": "refresh-only"}
    })

    with pytest.raises(HTTPException) as error:
        main._login_with_totp()

    assert error.value.status_code == 502
    assert error.value.detail == "m.Stock authentication response did not contain an access token."


def test_gateway_secret_is_required(monkeypatch):
    monkeypatch.setenv("MSTOCK_GATEWAY_SECRET", "expected-secret")

    with pytest.raises(HTTPException) as error:
        main.require_gateway_secret("wrong-secret")

    assert error.value.status_code == 403
    assert error.value.detail == "Gateway authentication failed."
