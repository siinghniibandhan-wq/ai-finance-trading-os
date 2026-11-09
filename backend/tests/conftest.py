"""Safe defaults for unit-test imports; never point tests at production."""
import os

# The application creates its SQLAlchemy engine during import. Unit tests use
# their own temporary SQLite databases, so provide a harmless import-time URL.
# PostgreSQL integration tests separately require BROKER_TEST_DATABASE_URL.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/financial-os-unit-test-import.db")

# Market-data unit tests mock the gateway transport. Provide a non-production
# base URL so request construction is valid without contacting a live service.
os.environ.setdefault("MSTOCK_GATEWAY_URL", "http://127.0.0.1:8000")
