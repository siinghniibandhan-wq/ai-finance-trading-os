"""Regression tests for trusted reverse-proxy client IP extraction."""
from starlette.requests import Request

from app.routes.auth import _client_ip


def _request(x_forwarded_for: str = "", client_host: str = "127.0.0.1") -> Request:
    headers = []
    if x_forwarded_for:
        headers.append((b"x-forwarded-for", x_forwarded_for.encode("ascii")))
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/api/auth/login",
        "raw_path": b"/api/auth/login",
        "query_string": b"",
        "headers": headers,
        "client": (client_host, 12345),
        "server": ("testserver", 443),
    })


def test_trusted_single_proxy_uses_client_ip_before_proxy(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "1")
    request = _request("198.51.100.10, 10.0.0.5")

    assert _client_ip(request) == "198.51.100.10"


def test_trusted_multiple_proxies_uses_last_untrusted_hop(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "2")
    request = _request("203.0.113.99, 198.51.100.10, 10.0.0.4, 10.0.0.5")

    assert _client_ip(request) == "198.51.100.10"


def test_untrusted_forwarded_header_is_ignored(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "0")
    request = _request("198.51.100.10")

    assert _client_ip(request) == "127.0.0.1"
