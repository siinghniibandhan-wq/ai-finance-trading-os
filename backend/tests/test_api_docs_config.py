from app.api_docs import api_docs_enabled


def test_api_docs_are_disabled_by_default_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENABLE_API_DOCS", raising=False)

    assert api_docs_enabled() is False


def test_api_docs_can_be_explicitly_enabled(monkeypatch):
    for value in ("1", "true", "YES", "on"):
        monkeypatch.setenv("ENABLE_API_DOCS", value)
        assert api_docs_enabled() is True


def test_api_docs_accepts_explicit_false_values(monkeypatch):
    for value in ("0", "false", "NO", "off"):
        monkeypatch.setenv("ENABLE_API_DOCS", value)
        assert api_docs_enabled() is False
