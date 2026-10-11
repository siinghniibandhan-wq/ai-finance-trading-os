"""Regression tests for capital-gains eligibility and review safeguards."""
from decimal import Decimal

from app.routes.tax_calculation import (
    lot_has_section_111a_confirmation,
    requires_capital_gains_review,
)


def test_request_wide_stt_flag_does_not_confirm_section_111a_per_lot():
    # A request-level confirmation is intentionally not accepted as lot evidence.
    lot = {}
    transaction = {"stt_confirmed": True}
    assert lot_has_section_111a_confirmation(lot, transaction) is False


def test_explicit_lot_level_section_111a_confirmation_is_recognized():
    lot = {"section_111a_eligibility_confirmed": True}
    assert lot_has_section_111a_confirmation(lot, {}) is True


def test_zero_unclassified_gain_still_requires_review():
    assert requires_capital_gains_review(
        has_unclassified_lot=True,
        unclassified_amount=Decimal("0.00"),
        has_unmatched_lots=False,
        unmatched_quantity=Decimal("0"),
    ) is True


def test_negative_unclassified_gain_still_requires_review():
    assert requires_capital_gains_review(
        has_unclassified_lot=True,
        unclassified_amount=Decimal("-25.00"),
        has_unmatched_lots=False,
        unmatched_quantity=Decimal("0"),
    ) is True


def test_unmatched_quantity_requires_review_even_when_gain_is_zero():
    assert requires_capital_gains_review(
        has_unclassified_lot=False,
        unclassified_amount=Decimal("0.00"),
        has_unmatched_lots=False,
        unmatched_quantity=Decimal("2"),
    ) is True
