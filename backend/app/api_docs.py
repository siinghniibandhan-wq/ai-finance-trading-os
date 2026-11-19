"""Environment configuration for interactive API documentation."""

import os


def api_docs_enabled() -> bool:
    """Keep API docs disabled by default; require explicit ENABLE_API_DOCS opt-in."""
    return os.getenv("ENABLE_API_DOCS", "0").strip().lower() in {"1", "true", "yes", "on"}
