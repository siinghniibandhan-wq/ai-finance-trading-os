import pytest

from app.services.market_intelligence import (
    classify_futures_position,
    calculate_option_metrics,
    score_conviction,
    aggregate_sector_strength,
)


@pytest.mark.parametrize(
    ("price_change_pct", "oi_change_pct", "expected"),
    [
        (1.2, 2.4, "long_build_up"),
        (-1.2, 2.4, "short_build_up"),
        (1.2, -2.4, "short_covering"),
        (-1.2, -2.4, "long_unwinding"),
        (0.0, 2.0, "neutral"),
        (None, 2.0, "insufficient_data"),
    ],
)
def test_classifies_futures_position_from_price_and_oi_changes(
    price_change_pct, oi_change_pct, expected
):
    assert classify_futures_position(price_change_pct, oi_change_pct) == expected


def test_option_metrics_calculates_pcr_support_and_resistance():
    rows = [
        {"strike": 22000, "call_oi": 100, "put_oi": 500},
        {"strike": 22100, "call_oi": 900, "put_oi": 300},
        {"strike": 22200, "call_oi": 700, "put_oi": 200},
    ]

    result = calculate_option_metrics(rows)

    assert result["total_call_oi"] == 1700
    assert result["total_put_oi"] == 1000
    assert result["put_call_ratio"] == pytest.approx(1000 / 1700)
    assert result["support_strike"] == 22000
    assert result["resistance_strike"] == 22100


def test_option_metrics_rejects_invalid_or_empty_chain():
    with pytest.raises(ValueError):
        calculate_option_metrics([])
    with pytest.raises(ValueError):
        calculate_option_metrics([{"strike": -1, "call_oi": 1, "put_oi": 1}])


def test_conviction_score_uses_five_independent_confirmations():
    result = score_conviction(
        positions_opened=True,
        spot_agrees=True,
        last_hour_agrees=False,
        option_writers_agree=True,
        sector_agrees=True,
    )

    assert result == {
        "score": 4,
        "out_of": 5,
        "percentage": 80,
        "label": "high",
        "checks": {
            "positions_opened": True,
            "spot_agrees": True,
            "last_hour_agrees": False,
            "option_writers_agree": True,
            "sector_agrees": True,
        },
    }


def test_sector_strength_aggregates_breadth_and_average_move():
    result = aggregate_sector_strength(
        [
            {"sector": "IT", "symbol": "A", "change_pct": 2.0},
            {"sector": "IT", "symbol": "B", "change_pct": -1.0},
            {"sector": "BANK", "symbol": "C", "change_pct": 1.0},
        ]
    )

    assert result[0]["sector"] == "BANK"
    assert result[0]["advancers"] == 1
    assert result[0]["decliners"] == 0
    assert result[0]["average_change_pct"] == pytest.approx(1.0)
    assert result[1]["sector"] == "IT"
    assert result[1]["advancers"] == 1
    assert result[1]["decliners"] == 1
