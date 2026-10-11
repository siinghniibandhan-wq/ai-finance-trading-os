"""Regression tests for fail-closed financial-year rule selection."""
import pytest

from app.routes.final_tax_liability import get_tax_rule_set


def test_current_supported_financial_year_has_explicit_rule_set():
    rules = get_tax_rule_set("2026-27")
    assert rules["rule_set_id"] == "IN-INDIVIDUAL-2026-27-v1"
    assert rules["review_status"] == "supported_with_conditional_capital_gains"


@pytest.mark.parametrize("financial_year", ["2025-26", "2027-28", "2030-31"])
def test_unsupported_financial_year_is_not_calculated_with_current_rules(financial_year):
    with pytest.raises(ValueError, match="Tax rules are not configured"):
        get_tax_rule_set(financial_year)


@pytest.mark.parametrize("financial_year", ["2026/27", "abc", "2026-28"])
def test_invalid_financial_year_format_is_rejected(financial_year):
    with pytest.raises(ValueError):
        get_tax_rule_set(financial_year)
