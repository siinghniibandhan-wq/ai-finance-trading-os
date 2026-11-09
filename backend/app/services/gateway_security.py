"""Validate transport security for backend-to-broker-gateway requests."""

from urllib.parse import urlsplit


def require_secure_gateway_url(base_url: str) -> str:
    """Allow HTTPS remote gateways or plain HTTP on the same host only."""
    value = (base_url or "").strip().rstrip("/")
    if not value:
        raise ValueError("MSTOCK_GATEWAY_URL is not configured.")

    parsed = urlsplit(value)
    loopback_http = (
        parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost"}
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )
    secure_remote = (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )
    if not (loopback_http or secure_remote):
        raise ValueError(
            "MSTOCK_GATEWAY_URL must use HTTPS; HTTP is allowed only for a loopback service."
        )
    return value


def require_gateway_secret(secret: str) -> str:
    """Require a strong server-side shared secret for gateway-to-backend calls."""
    value = (secret or "").strip()
    if len(value) < 32:
        raise ValueError("MSTOCK_GATEWAY_SECRET must be configured with at least 32 characters.")
    return value
