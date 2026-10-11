"""Focused tests for surcharge marginal relief safeguards."""
from decimal import Decimal

from app.routes.final_tax_liability import calculate_surcharge


def test_surcharge_below_threshold_has_no_marginal_relief():
    result = calculate_surcharge(4_900_000, 1_000_000, 0, "new")
    assert result["total"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("0.00")
    assert result["marginal_relief_review_required"] is False


def test_surcharge_threshold_relief_is_reported_for_normal_income():
    # For a tiny amount over ₹50 lakh, surcharge is limited so tax does
    # not jump beyond tax at the threshold plus the excess income.
    result = calculate_surcharge(5_000_100, 1_140_000, 0, "new")
    assert result["marginal_relief_threshold"] == 5_000_000
    assert result["marginal_relief"] > Decimal("0.00")
    assert result["total"] >= Decimal("0.00")


def test_special_rate_income_requires_exact_composition_review():
    result = calculate_surcharge(5_000_100, 1_000_000, 100_000, "new")
    assert result["marginal_relief_review_required"] is True
    assert result["marginal_relief"] == Decimal("0.00")
