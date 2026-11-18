from app.routes.market_charts import _normalize_chart_candles


def test_preserves_ohlc_candles_when_provider_omits_volume():
    assert _normalize_chart_candles([
        ["2026-11-18T09:15:00+05:30", 100, 105, 99, 103],
    ]) == [
        {
            "timestamp": "2026-11-18T09:15:00+05:30",
            "open": 100,
            "high": 105,
            "low": 99,
            "close": 103,
            "volume": None,
        }
    ]


def test_preserves_provider_volume_when_present():
    assert _normalize_chart_candles([
        ["2026-11-18T09:15:00+05:30", 100, 105, 99, 103, 1200],
    ])[0]["volume"] == 1200


def test_ignores_malformed_historical_candle_rows():
    assert _normalize_chart_candles([["2026-11-18T09:15:00+05:30", 100, 105]]) == []
