"""Focused regression tests for old-regime age-based slab calculations."""

from decimal import Decimal

from app.routes.final_tax_liability import calculate_old_regime_slab_tax


def test_under_60_old_regime_slabs():
    assert calculate_old_regime_slab_tax(250000) == Decimal("0.00")
    assert calculate_old_regime_slab_tax(500000) == Decimal("12500.00")


def test_resident_senior_citizen_basic_exemption():
    assert calculate_old_regime_slab_tax(
        300000, age_category="60_to_79", residential_status="resident"
    ) == Decimal("0.00")
    assert calculate_old_regime_slab_tax(
        500000, age_category="60_to_79", residential_status="resident"
    ) == Decimal("10000.00")


def test_resident_super_senior_basic_exemption():
    assert calculate_old_regime_slab_tax(
        500000, age_category="80_plus", residential_status="resident"
    ) == Decimal("0.00")
    assert calculate_old_regime_slab_tax(
        1000000, age_category="80_plus", residential_status="resident"
    ) == Decimal("100000.00")


def test_nonresident_does_not_get_age_based_exemption():
    assert calculate_old_regime_slab_tax(
        300000, age_category="80_plus", residential_status="non_resident"
    ) == Decimal("2500.00")
