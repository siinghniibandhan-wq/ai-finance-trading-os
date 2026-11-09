import pytest

from app.services.gateway_security import require_secure_gateway_url


def test_remote_https_gateway_is_allowed():
    assert require_secure_gateway_url("https://gateway.example.com") == "https://gateway.example.com"


@pytest.mark.parametrize("url", ["http://127.0.0.1:8000", "http://localhost:8000"])
def test_loopback_http_gateway_is_allowed(url):
    assert require_secure_gateway_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://gateway.example.com:8000",
        "http://54.153.201.74:8000",
        "https://user:password@gateway.example.com",
        "https://gateway.example.com/path?token=secret",
    ],
)
def test_insecure_or_ambiguous_gateway_urls_are_rejected(url):
    with pytest.raises(ValueError):
        require_secure_gateway_url(url)


def test_gateway_secret_must_be_present_and_strong():
    from app.services.gateway_security import require_gateway_secret

    with pytest.raises(ValueError):
        require_gateway_secret("")
    with pytest.raises(ValueError):
        require_gateway_secret("short")
    assert len(require_gateway_secret("x" * 48)) == 48
