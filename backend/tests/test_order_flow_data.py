from datetime import datetime, timezone, timedelta

import pytest

from app.services.order_flow_data import (
    aggregate_contract_months,
    calculate_oi_change,
    aggregate_option_oi,
    feed_status,
)


def test_contract_months_aggregate_by_expiry_and_sum_volume_and_oi():
    rows = [
        {"symbol": "NIFTY", "expiry": "2026-11-26", "volume": 10, "oi": 100},
        {"symbol": "NIFTY", "expiry": "2026-11-26", "volume": 20, "oi": 200},
        {"symbol": "NIFTY", "expiry": "2026-12-31", "volume": 5, "oi": 50},
    ]
    result = aggregate_contract_months(rows)
    assert result == [
        {"symbol": "NIFTY", "expiry": "2026-11-26", "contracts": 2, "volume": 30, "oi": 300},
        {"symbol": "NIFTY", "expiry": "2026-12-31", "contracts": 1, "volume": 5, "oi": 50},
    ]


def test_oi_change_uses_previous_oi_and_handles_zero_baseline():
    assert calculate_oi_change(120, 100) == {"change": 20, "change_pct": 20.0}
    assert calculate_oi_change(120, 0) == {"change": 120, "change_pct": None}


def test_option_oi_aggregates_by_underlying_expiry_and_strike_without_mixing_contracts():
    rows = [
        {"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25000, "option_type": "CE", "oi": 100},
        {"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25000, "option_type": "PE", "oi": 150},
        {"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25000, "option_type": "CE", "oi": 25},
        {"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25100, "option_type": "PE", "oi": 75},
        {"symbol": "BANKNIFTY", "expiry": "2026-11-26", "strike": 25000, "option_type": "CE", "oi": 40},
        {"symbol": "NIFTY", "expiry": "2026-12-31", "strike": 25000, "option_type": "PE", "oi": 30},
    ]
    assert aggregate_option_oi(rows) == [
        {"symbol": "BANKNIFTY", "expiry": "2026-11-26", "strike": 25000, "ce_oi": 40, "pe_oi": 0},
        {"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25000, "ce_oi": 125, "pe_oi": 150},
        {"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25100, "ce_oi": 0, "pe_oi": 75},
        {"symbol": "NIFTY", "expiry": "2026-12-31", "strike": 25000, "ce_oi": 0, "pe_oi": 30},
    ]


def test_feed_status_distinguishes_fresh_stale_and_missing_ticks():
    now = datetime(2026, 11, 13, 10, 0, tzinfo=timezone.utc)
    assert feed_status(now - timedelta(seconds=4), now=now, stale_after_seconds=10)["status"] == "fresh"
    assert feed_status(now - timedelta(seconds=15), now=now, stale_after_seconds=10)["status"] == "stale"
    assert feed_status(None, now=now, stale_after_seconds=10)["status"] == "disconnected"


def test_invalid_option_side_is_rejected():
    with pytest.raises(ValueError):
        aggregate_option_oi([{"symbol": "NIFTY", "expiry": "2026-11-26", "strike": 25000, "option_type": "XX", "oi": 1}])
