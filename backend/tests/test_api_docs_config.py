from app.api_docs import api_docs_enabled


def test_api_docs_can_be_enabled_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_API_DOCS", "1")

    assert api_docs_enabled() is True


def test_api_docs_remain_disabled_without_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("ENABLE_API_DOCS", raising=False)

    assert api_docs_enabled() is False


def test_api_docs_accepts_common_true_values(monkeypatch):
    for value in ("true", "YES", "on"):
        monkeypatch.setenv("ENABLE_API_DOCS", value)
        assert api_docs_enabled() is True
