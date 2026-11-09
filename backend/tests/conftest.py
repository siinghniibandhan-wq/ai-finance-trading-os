"""Safe defaults for unit-test imports; never point tests at production."""
import os

# The application creates its SQLAlchemy engine during import. Unit tests use
# their own temporary SQLite databases, so provide a harmless import-time URL.
# PostgreSQL integration tests separately require BROKER_TEST_DATABASE_URL.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/financial-os-unit-test-import.db")
