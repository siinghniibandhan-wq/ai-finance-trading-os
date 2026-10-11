"""Regression tests for Section 87A rebate and New Regime marginal relief."""
from decimal import Decimal

from app.routes.final_tax_liability import calculate_87a_rebate


def test_new_regime_full_rebate_at_12_lakh():
    result = calculate_87a_rebate(1_200_000, 60_000, "new", "resident")
    assert result["rebate"] == Decimal("60000.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_new_regime_marginal_relief_just_above_threshold():
    # Example normal slab tax is ₹60,100 at income ₹12,00,100.
    result = calculate_87a_rebate(1_200_100, 60_100, "new", "resident")
    assert result["rebate"] == Decimal("60000.00")
    assert result["marginal_relief"] == Decimal("60000.00")
    assert Decimal("60100") - result["rebate"] <= Decimal("100")


def test_old_regime_does_not_get_new_regime_marginal_relief():
    result = calculate_87a_rebate(510_000, 13_500, "old", "resident")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_nonresident_not_eligible_for_87a():
    result = calculate_87a_rebate(500_000, 12_500, "old", "non_resident")
    assert result["eligible"] is False
    assert result["rebate"] == Decimal("0.00")
