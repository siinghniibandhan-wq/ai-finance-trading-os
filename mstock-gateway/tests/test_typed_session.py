from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

import main

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(main, "STATIC_ACCESS_TOKEN", "")
    monkeypatch.setattr(main, "API_KEY", "api-key")
    monkeypatch.setattr(main, "TOTP_SECRET", "")
    monkeypatch.setattr(main, "_cached_access_token", None)
    monkeypatch.setattr(main, "_cached_token_expires_at", None)
    monkeypatch.setattr(main, "_load_session", lambda: None)
    monkeypatch.setattr(main, "_store_session", lambda token, exp: True)
    monkeypatch.setattr(main, "_clear_session", lambda: None)


def test_invalid_base32_seed_does_not_crash_and_asks_for_typed_code(monkeypatch):
    monkeypatch.setattr(main, "TOTP_SECRET", "otpauth://totp/not-base32?secret=!!")
    with pytest.raises(HTTPException) as error:
        main._get_access_token()
    assert error.value.status_code == 503
    assert error.value.detail.startswith(main.SESSION_REQUIRED_PREFIX)


def test_typed_code_creates_session_that_is_reused_without_new_code(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "_post_totp_session", lambda code: calls.append(code) or {
        "status": "success", "data": {"access_token": "tok-1"}})
    result = main.create_session(main.SessionRequest(totp="123456"))
    assert result["connected"] is True
    assert main._get_access_token() == "tok-1"
    assert main._get_access_token() == "tok-1"
    assert calls == ["123456"]


def test_rejects_non_six_digit_code(monkeypatch):
    with pytest.raises(HTTPException) as error:
        main.create_session(main.SessionRequest(totp="12ab56"))
    assert error.value.status_code == 400


def test_rejected_code_returns_400_and_stores_nothing(monkeypatch):
    monkeypatch.setattr(main, "_post_totp_session", lambda code: {
        "status": "error", "message": "Please enter correct TOTP", "data": None})
    with pytest.raises(HTTPException) as error:
        main.create_session(main.SessionRequest(totp="123456"))
    assert error.value.status_code == 400
    assert main._cached_access_token is None


def test_new_instance_uses_shared_stored_session(monkeypatch):
    expires = datetime.now(IST) + timedelta(hours=3)
    monkeypatch.setattr(main, "_load_session", lambda: ("shared-token", expires))
    assert main._get_access_token() == "shared-token"


def test_expired_stored_session_requires_new_code(monkeypatch):
    expired = datetime.now(IST) - timedelta(minutes=1)
    monkeypatch.setattr(main, "_load_session", lambda: ("old", expired))
    with pytest.raises(HTTPException) as error:
        main._get_access_token()
    assert error.value.detail.startswith(main.SESSION_REQUIRED_PREFIX)


def test_token_rejected_by_mstock_clears_session_and_requires_new_code(monkeypatch):
    cleared = []
    monkeypatch.setattr(main, "_cached_access_token", "bad")
    monkeypatch.setattr(main, "_cached_token_expires_at", datetime.now(IST) + timedelta(hours=1))
    monkeypatch.setattr(main, "_clear_session", lambda: cleared.append(True))
    with pytest.raises(HTTPException):
        main._get_access_token(force_refresh=True)
    assert cleared == [True]


def test_session_status_never_returns_token(monkeypatch):
    monkeypatch.setattr(main, "_cached_access_token", "secret-token")
    monkeypatch.setattr(main, "_cached_token_expires_at", datetime.now(IST) + timedelta(hours=1))
    assert "secret-token" not in str(main.session_status())
