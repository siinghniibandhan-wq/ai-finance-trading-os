"""Regression tests for financial-year-driven capital-gains tax settings."""
from decimal import Decimal

from app.routes.tax_calculation import calculate_tax
from app.routes.final_tax_liability import get_tax_rule_set


def test_tax_calculation_uses_passed_financial_year_rates_and_threshold():
    rules = get_tax_rule_set("2026-27")
    cg = rules["capital_gains"]
    result = calculate_tax(
        stcg=Decimal("10000"),
        ltcg=Decimal("150000"),
        stt_confirmed=True,
        stcg_rate=Decimal(cg["section_111a_rate"]),
        ltcg_rate=Decimal(cg["section_112a_rate"]),
        ltcg_exemption_limit=Decimal(cg["section_112a_annual_exemption"]),
        cess_rate=Decimal(rules["cess_rate"]),
    )
    assert result["stcg"]["tax"] == Decimal("2000.00")
    assert result["ltcg"]["taxable_gain"] == Decimal("25000")
    assert result["ltcg"]["tax"] == Decimal("3125.00")
    assert result["summary"]["health_education_cess"] == Decimal("205.00")


def test_unconfirmed_stt_does_not_apply_section_111a_rate():
    result = calculate_tax(
        stcg=Decimal("10000"),
        ltcg=Decimal("0"),
        stt_confirmed=False,
    )
    assert result["stcg"]["tax"] == Decimal("0.00")
    assert result["stcg"]["status"] == "requires_stt_confirmation"
