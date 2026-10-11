"""Regression tests for fail-closed Section 112A eligibility handling."""
from decimal import Decimal

from app.routes.tax_calculation import calculate_tax


def test_ltcg_is_not_taxed_at_section_112a_rate_without_eligibility_confirmation():
    result = calculate_tax(
        stcg=Decimal("0"), ltcg=Decimal("200000"), stt_confirmed=False,
        section_112a_eligibility_confirmed=False,
    )
    assert result["ltcg"]["tax"] == Decimal("0.00")
    assert result["ltcg"]["status"] == "requires_section_112a_eligibility_confirmation"


def test_ltcg_special_rate_applies_only_when_eligibility_is_confirmed():
    result = calculate_tax(
        stcg=Decimal("0"), ltcg=Decimal("200000"), stt_confirmed=False,
        section_112a_eligibility_confirmed=True,
    )
    assert result["ltcg"]["taxable_gain"] == Decimal("75000.00")
    assert result["ltcg"]["tax"] == Decimal("9375.00")
    assert result["ltcg"]["status"] == "calculated_eligibility_confirmed"
