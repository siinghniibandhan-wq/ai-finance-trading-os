"""Safe defaults for unit-test imports; never point tests at production."""
import os

# The application creates its SQLAlchemy engine during import. Unit tests use
# their own temporary SQLite databases, so provide a harmless import-time URL.
# PostgreSQL integration tests separately require BROKER_TEST_DATABASE_URL.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/financial-os-unit-test-import.db")
# A non-routable test-only URL lets gateway clients build request objects while
# their network calls are replaced with mocks in unit tests. Production code
# intentionally has no legacy public-IP fallback.
os.environ.setdefault("MSTOCK_GATEWAY_URL", "https://gateway.invalid")
