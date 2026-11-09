"""Focused tests for failed-login throttling policy."""

import pytest
from fastapi import HTTPException

from app.routes import auth


def setup_function():
    auth._failed_login_attempts.clear()


def test_fifth_failed_login_blocks_the_next_attempt_for_same_account_across_ips():
    for index in range(5):
        auth._record_failed_login("user@example.test", f"198.51.100.{index + 1}")

    with pytest.raises(HTTPException) as error:
        auth._check_failed_login_limits("user@example.test", "203.0.113.10")

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "900"


def test_ip_limit_applies_across_different_login_identifiers():
    for index in range(20):
        auth._record_failed_login(f"user{index}@example.test", "198.51.100.10")

    with pytest.raises(HTTPException) as error:
        auth._check_failed_login_limits("another@example.test", "198.51.100.10")

    assert error.value.status_code == 429


def test_successful_login_clears_account_failures_but_not_ip_failures():
    for _ in range(5):
        auth._record_failed_login("user@example.test", "198.51.100.10")
    for index in range(15):
        auth._record_failed_login(f"other{index}@example.test", "198.51.100.10")

    auth._clear_failed_login("user@example.test")

    # Account can try again, but the IP's accumulated failures remain.
    auth._check_failed_login_limits("user@example.test", "203.0.113.10")
    with pytest.raises(HTTPException) as error:
        auth._check_failed_login_limits("another@example.test", "198.51.100.10")
    assert error.value.status_code == 429
