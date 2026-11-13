from fastapi import HTTPException

from app.routes.market_order_flow import analyze_market_order_flow


def test_order_flow_analysis_returns_futures_options_and_sector_signals():
    result = analyze_market_order_flow({
        "futures": [
            {"symbol": "RELIANCE", "price_change_pct": 1.5, "oi_change_pct": 2.0}
        ],
        "options": [
            {"strike": 22000, "call_oi": 100, "put_oi": 500},
            {"strike": 22100, "call_oi": 900, "put_oi": 300},
        ],
        "sectors": [
            {"sector": "BANK", "symbol": "A", "change_pct": 1.0},
            {"sector": "BANK", "symbol": "B", "change_pct": -0.5},
        ],
    })

    assert result["read_only"] is True
    assert result["database_write"] is False
    assert result["futures"][0]["position"] == "long_build_up"
    assert result["options"]["support_strike"] == 22000
    assert result["options"]["resistance_strike"] == 22100
    assert result["sectors"][0]["sector"] == "BANK"


def test_order_flow_analysis_rejects_empty_market_payload():
    try:
        analyze_market_order_flow({})
    except HTTPException as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Empty market payload must be rejected")
