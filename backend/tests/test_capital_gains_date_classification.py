"""Tests for calendar-date and per-FIFO-lot capital-gains classification."""
from datetime import date

from app.routes.capital_gains_classification import classify_gain_by_dates


def test_listed_equity_exactly_twelve_calendar_months_is_short_term():
    result = classify_gain_by_dates(date(2025, 1, 31), date(2026, 1, 31), "listed_equity")
    assert result["classification"] == "STCG"
    assert result["threshold_date"] == "2026-01-31"


def test_listed_equity_after_twelve_calendar_months_is_long_term():
    result = classify_gain_by_dates(date(2025, 1, 31), date(2026, 2, 1), "listed_equity")
    assert result["classification"] == "LTCG"


def test_month_end_threshold_clamps_for_short_month():
    result = classify_gain_by_dates(date(2025, 1, 31), date(2026, 1, 28), "listed_equity")
    assert result["threshold_date"] == "2026-01-31"
    assert result["classification"] == "STCG"


def test_unknown_asset_and_invalid_dates_are_not_guessed():
    assert classify_gain_by_dates(date(2025, 1, 1), date(2026, 2, 1), "unknown") ["classification"] == "UNCLASSIFIED"
    assert classify_gain_by_dates(date(2026, 1, 1), date(2025, 1, 1), "listed_equity")["classification_status"] == "sale_before_acquisition"
    assert classify_gain_by_dates(None, date(2026, 1, 1), "listed_equity")["classification"] == "UNCLASSIFIED"
