"""Environment configuration for interactive API documentation."""

import os


def api_docs_enabled() -> bool:
    """Enable API docs by default; set ENABLE_API_DOCS=0 to disable them."""
    return os.getenv("ENABLE_API_DOCS", "1").strip().lower() not in {"0", "false", "no", "off"}
