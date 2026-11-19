"""Environment configuration for interactive API documentation."""

import os


def api_docs_enabled() -> bool:
    """Return whether API docs are explicitly enabled in any deployment environment."""
    return os.getenv("ENABLE_API_DOCS", "").strip().lower() in {"1", "true", "yes", "on"}
