"""Regression tests for verified exempt-income claim handling."""
from decimal import Decimal
from types import SimpleNamespace

from app.routes.deductions_exempt_income import (
    EXEMPT_INCOME_CATALOG, HRAInputs, calculate_hra_exemption, classify_hra_city, regime_available,
)
from app.routes.final_taxable_income import aggregate_verified_exempt_claims, calculate_salary_record_hra_exemption


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
        rent_actually_paid=True,
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
        rent_actually_paid=True,
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
        rent_actually_paid=True,
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
        rent_actually_paid=True,
        city="Patna",
    )
    result = calculate_hra_exemption(inputs, "old")
    assert result["calculated_exemption"] == "0.00"


def test_hra_calculation_rejects_zero_eligible_salary():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("0"),
        annual_hra_received=Decimal("100000"),
        annual_rent_paid=Decimal("120000"),
        rent_actually_paid=True,
        city="Patna",
    )
    try:
        calculate_hra_exemption(inputs, "old")
    except ValueError as exc:
        assert "positive annual basic salary" in str(exc)
    else:
        raise AssertionError("Zero eligible salary must be rejected")


def test_hra_city_classification_is_automatic_and_alias_aware():
    assert classify_hra_city("Mumbai", "2025-26") == "metro"
    assert classify_hra_city(" New Delhi ", "2025-26") == "metro"
    assert classify_hra_city("Dhanbad", "2026-27") == "non_metro"
    assert classify_hra_city("An Unlisted City", "2026-27") == "non_metro"


def test_hra_city_rules_change_by_financial_year():
    # FY 2025-26 uses the traditional four-city list.
    assert classify_hra_city("Bengaluru", "2025-26") == "non_metro"
    assert classify_hra_city("Hyderabad", "2025-26") == "non_metro"
    # Rule 279 from FY 2026-27 extends the 50% limit to four more cities.
    for city in ("Bengaluru", "Bangalore", "Hyderabad", "Pune", "Ahmedabad"):
        assert classify_hra_city(city, "2026-27") == "metro"


def test_unknown_financial_year_does_not_grant_expanded_city_limit():
    assert classify_hra_city("Bengaluru", "invalid") == "non_metro"


def test_hra_calculation_ignores_client_supplied_city_classification():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_hra_received=Decimal("300000"),
        annual_rent_paid=Decimal("500000"),
        rent_actually_paid=True,
        city="Patna",
        city_classification="metro",
    )
    result = calculate_hra_exemption(inputs, "old", "2026-27")
    assert result["city_classification"] == "non_metro"
    assert result["metro_city_for_hra"] is False
    assert result["limits"]["salary_percentage_limit"] == "240000.00"


def test_hra_calculation_requires_confirmation_rent_was_actually_paid():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_hra_received=Decimal("200000"),
        annual_rent_paid=Decimal("180000"),
        city="Delhi",
    )
    try:
        calculate_hra_exemption(inputs, "old")
    except ValueError as exc:
        assert "rent was actually paid" in str(exc)
    else:
        raise AssertionError("HRA calculation must require rent-paid confirmation")


def test_hra_calculation_rejects_taxpayer_owned_accommodation():
    inputs = HRAInputs(
        annual_basic_salary=Decimal("600000"),
        annual_hra_received=Decimal("200000"),
        annual_rent_paid=Decimal("180000"),
        accommodation_owned_by_taxpayer=True,
        rent_actually_paid=True,
        city="Delhi",
    )
    try:
        calculate_hra_exemption(inputs, "old")
    except ValueError as exc:
        assert "accommodation owned" in str(exc)
    else:
        raise AssertionError("HRA calculation must reject taxpayer-owned accommodation")



def salary_record(**overrides):
    values = {
        "annual_basic_salary": Decimal("600000"),
        "annual_da_forming_retirement_benefits": Decimal("0"),
        "annual_commission_on_turnover_at_fixed_percentage": Decimal("0"),
        "annual_hra_received": Decimal("240000"),
        "annual_rent_paid": Decimal("240000"),
        "accommodation_owned_by_taxpayer": False,
        "rent_actually_paid": True,
        "city": "Delhi",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_verified_salary_record_hra_uses_rent_and_ownership_confirmations():
    result = calculate_salary_record_hra_exemption(salary_record(), "2026-27")
    assert result["calculated_exemption"] == "180000.00"
    assert result["rent_actually_paid"] is True
    assert result["accommodation_owned_by_taxpayer"] is False


def test_salary_record_hra_is_blocked_when_rent_confirmation_is_missing():
    try:
        calculate_salary_record_hra_exemption(
            salary_record(rent_actually_paid=False), "2026-27"
        )
    except ValueError as exc:
        assert "rent was actually paid" in str(exc)
    else:
        raise AssertionError("HRA must require explicit rent-paid confirmation")


def test_salary_record_hra_is_blocked_when_taxpayer_owns_accommodation():
    try:
        calculate_salary_record_hra_exemption(
            salary_record(accommodation_owned_by_taxpayer=True), "2026-27"
        )
    except ValueError as exc:
        assert "accommodation owned" in str(exc)
    else:
        raise AssertionError("HRA must reject taxpayer-owned accommodation")
