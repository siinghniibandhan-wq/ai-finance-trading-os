from app.services.mstock_stream_runtime import build_stream_url, get_stream_config


def test_stream_is_disabled_by_default_and_does_not_require_credentials():
    config = get_stream_config({})
    assert config["enabled"] is False
    assert config["configured"] is False


def test_stream_requires_secure_endpoint_credentials_and_instrument_tokens():
    base = {
        "MSTOCK_STREAM_ENABLED": "true",
        "MSTOCK_STREAM_API_KEY": "api-key",
        "MSTOCK_STREAM_ACCESS_TOKEN": "access-token",
        "MSTOCK_STREAM_INSTRUMENT_TOKENS": "101, 202,101",
    }
    config = get_stream_config(base)
    assert config["configured"] is True
    assert config["tokens"] == [101, 202]
    assert "api-key" not in str({key: value for key, value in config.items() if key not in {"api_key"}})


def test_stream_rejects_invalid_tokens_and_non_tls_endpoint():
    invalid_tokens = get_stream_config({
        "MSTOCK_STREAM_ENABLED": "true",
        "MSTOCK_STREAM_API_KEY": "key",
        "MSTOCK_STREAM_ACCESS_TOKEN": "token",
        "MSTOCK_STREAM_INSTRUMENT_TOKENS": "101,not-a-token",
    })
    assert invalid_tokens["configured"] is False
    assert "positive integers" in invalid_tokens["reason"]

    try:
        build_stream_url("ws://insecure.example", "key", "token")
    except ValueError as exc:
        assert "secure WSS" in str(exc)
    else:
        raise AssertionError("Insecure WebSocket endpoint must be rejected")


def test_builds_official_mstock_type_a_auth_url_with_encoded_credentials():
    url = build_stream_url("wss://ws.mstock.trade", "api key", "access/token")
    assert url == "wss://ws.mstock.trade?API_KEY=api+key&ACCESS_TOKEN=access%2Ftoken"


from app.routes.market_options import _parse_side, get_option_chain


def test_option_chain_normalizes_provider_call_and_put_rows_by_strike(monkeypatch):
    import app.routes.market_options as route
    monkeypatch.setattr(route, "_provider_get", lambda path: {
        "contractModel": {"sym": "NIFTY"},
        "spot": "NIFTY,26000,NSEIDX",
        "call": ["1001,2200000,120", "1002,2210000,80"],
        "put": ["1003,2200000,240", "1004,2220000,50"],
    })
    result = get_option_chain(exchange=2, expiry=1795876200, token=26000)
    assert result["status"] == "success"
    assert result["underlying_symbol"] == "NIFTY"
    assert result["options"] == [
        {"strike": 22000.0, "call_oi": 120, "put_oi": 240},
        {"strike": 22100.0, "call_oi": 80, "put_oi": 0},
        {"strike": 22200.0, "call_oi": 0, "put_oi": 50},
    ]
    assert result["database_write"] is False


def test_option_chain_side_discards_malformed_and_negative_oi():
    rows = _parse_side(["1,2200000,100", "bad", "2,2210000,-5"], "call_oi")
    assert rows == {22000.0: {"strike": 22000.0, "call_oi": 100, "put_oi": 0}}
