"""Regression tests for verified exempt-income claim handling."""
from decimal import Decimal
from types import SimpleNamespace

from app.routes.deductions_exempt_income import (
    EXEMPT_INCOME_CATALOG, HRAInputs, calculate_hra_exemption, regime_available,
)
from app.routes.final_taxable_income import aggregate_verified_exempt_claims


def claim(key, amount, status="verified"):
    return SimpleNamespace(deduction_key=key, claimed_amount=Decimal(str(amount)), status=status)


def test_hra_is_old_regime_only_in_catalogue():
    hra = EXEMPT_INCOME_CATALOG["hra_exemption"]
    assert regime_available(hra, "old") is True
    assert regime_available(hra, "new") is False


def test_verified_old_regime_hra_claim_is_aggregated_with_disclosure():
    total, details = aggregate_verified_exempt_claims([claim("hra_exemption", "12500")], "old")
    assert total == Decimal("12500")
    assert details[0]["deduction_key"] == "hra_exemption"
    assert details[0]["user_confirmed_not_independently_validated"] is True
    assert "HRA calculator" in details[0]["calculation_note"]


def test_hra_claim_does_not_reduce_new_regime_taxable_income():
    total, details = aggregate_verified_exempt_claims([claim("hra_exemption", "12500")], "new")
    assert total == Decimal("0")
    assert details == []


def test_unknown_claim_key_is_not_applied_as_exempt_income():
    total, details = aggregate_verified_exempt_claims([claim("unknown_key", "9999")], "old")
    assert total == Decimal("0")
    assert details == []


def test_multiple_claims_for_same_exemption_are_aggregated():
    total, details = aggregate_verified_exempt_claims(
        [claim("hra_exemption", "1000"), claim("hra_exemption", "2500")], "old"
    )
    assert total == Decimal("3500")
    assert len(details) == 1
    assert details[0]["applied_amount"] == "3500"


def test_hra_calculation_uses_least_of_three_metro_limits():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_da_forming_retirement_benefits=Decimal("0"),
        annual_hra_received=Decimal("240000"),
        annual_rent_paid=Decimal("240000"),
        city="Delhi",
    )
    result = calculate_hra_exemption(inputs, "old")
    assert result["metro_city_for_hra"] is True
    assert result["limits"]["hra_received"] == "240000.00"
    assert result["limits"]["rent_paid_minus_10_percent_salary"] == "180000.00"
    assert result["limits"]["salary_percentage_limit"] == "300000.00"
    assert result["calculated_exemption"] == "180000.00"


def test_hra_calculation_uses_non_metro_40_percent_limit():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_hra_received=Decimal("300000"),
        annual_rent_paid=Decimal("500000"),
        city="Patna",
    )
    result = calculate_hra_exemption(inputs, "old")
    assert result["metro_city_for_hra"] is False
    assert result["calculated_exemption"] == "240000.00"


def test_hra_calculation_rejects_new_regime():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_hra_received=Decimal("200000"),
        annual_rent_paid=Decimal("180000"),
        city="Delhi",
    )
    try:
        calculate_hra_exemption(inputs, "new")
    except ValueError as exc:
        assert "not available" in str(exc)
    else:
        raise AssertionError("New regime must not permit HRA exemption")


def test_hra_calculation_returns_zero_when_rent_does_not_exceed_ten_percent_salary():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_hra_received=Decimal("100000"),
        annual_rent_paid=Decimal("50000"),
        city="Patna",
    )
    result = calculate_hra_exemption(inputs, "old")
    assert result["calculated_exemption"] == "0.00"


def test_hra_calculation_rejects_zero_eligible_salary():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("0"),
        annual_hra_received=Decimal("100000"),
        annual_rent_paid=Decimal("120000"),
        city="Patna",
    )
    try:
        calculate_hra_exemption(inputs, "old")
    except ValueError as exc:
        assert "positive annual basic salary" in str(exc)
    else:
        raise AssertionError("Zero eligible salary must be rejected")
