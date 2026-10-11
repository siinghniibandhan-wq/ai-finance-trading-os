"""Regression tests for Section 87A rebate and New Regime marginal relief."""
from decimal import Decimal

from app.routes.final_tax_liability import (
    calculate_87a_rebate,
    calculate_new_regime_slab_tax,
)


def test_new_regime_full_rebate_at_12_lakh():
    slab_tax = calculate_new_regime_slab_tax(1_200_000)
    result = calculate_87a_rebate(1_200_000, slab_tax, "new", "resident")
    assert slab_tax == Decimal("60000.00")
    assert result["rebate"] == Decimal("60000.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_new_regime_marginal_relief_is_separate_from_rebate():
    income = Decimal("1200100")
    slab_tax = calculate_new_regime_slab_tax(income)
    result = calculate_87a_rebate(income, slab_tax, "new", "resident")
    assert slab_tax == Decimal("60015.00")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("59915.00")
    assert slab_tax - result["marginal_relief"] == Decimal("100.00")


def test_no_marginal_relief_when_ordinary_tax_is_below_income_excess():
    result = calculate_87a_rebate(1_300_000, 50_000, "new", "resident")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_old_regime_does_not_get_new_regime_marginal_relief():
    result = calculate_87a_rebate(510_000, 13_500, "old", "resident")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_nonresident_not_eligible_for_87a():
    result = calculate_87a_rebate(500_000, 12_500, "old", "non_resident")
    assert result["eligible"] is False
    assert result["rebate"] == Decimal("0.00")
