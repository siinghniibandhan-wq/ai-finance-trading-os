"""Regression tests for verified exempt-income claim handling."""
from decimal import Decimal
from types import SimpleNamespace

from app.routes.deductions_exempt_income import EXEMPT_INCOME_CATALOG, regime_available
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
    assert "does not calculate the statutory HRA limit" in details[0]["calculation_note"]


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
