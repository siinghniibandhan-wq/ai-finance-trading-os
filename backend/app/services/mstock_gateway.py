"""Single source of truth for the deployed m.Stock Gateway connection.

The Financial OS backend and the m.Stock Gateway run on the same EC2 host.
Production config supplies MSTOCK_GATEWAY_URL=http://127.0.0.1:8000.
No stale public-IP fallback is permitted.
"""
import os

MSTOCK_GATEWAY_URL = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")
MSTOCK_GATEWAY_SECRET = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()


def require_mstock_gateway_url() -> str:
    """Return the configured Gateway base URL or fail closed."""
    if not MSTOCK_GATEWAY_URL:
        raise RuntimeError("MSTOCK_GATEWAY_URL is not configured.")
    return MSTOCK_GATEWAY_URL
