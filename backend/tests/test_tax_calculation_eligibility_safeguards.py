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


def test_negative_stcg_never_produces_negative_tax_or_cess():
    result = calculate_tax(
        stcg=Decimal("-50000"),
        ltcg=Decimal("0"),
        stt_confirmed=True,
        section_112a_eligibility_confirmed=False,
    )
    assert result["stcg"]["gross_gain"] == Decimal("-50000.00")
    assert result["stcg"]["taxable_gain"] == Decimal("0")
    assert result["stcg"]["tax"] == Decimal("0.00")
    assert result["summary"]["base_tax"] == Decimal("0.00")
    assert result["summary"]["health_education_cess"] == Decimal("0.00")
    assert result["summary"]["tax_plus_cess"] == Decimal("0.00")


def test_negative_stcg_does_not_reduce_tax_on_separately_confirmed_ltcg():
    result = calculate_tax(
        stcg=Decimal("-50000"),
        ltcg=Decimal("200000"),
        stt_confirmed=True,
        section_112a_eligibility_confirmed=True,
    )
    assert result["stcg"]["tax"] == Decimal("0.00")
    assert result["ltcg"]["tax"] == Decimal("9375.00")
    assert result["summary"]["base_tax"] == Decimal("9375.00")
    assert result["summary"]["health_education_cess"] == Decimal("375.00")
    assert result["summary"]["tax_plus_cess"] == Decimal("9750.00")
