"""Regression tests for capital-gains review propagation to final liability."""
from app.routes.final_tax_liability import get_capital_gains_review_reasons


def test_review_required_status_propagates():
    reasons = get_capital_gains_review_reasons({"status": "requires_review"})
    assert "capital_gains_engine_requires_review" in reasons


def test_unclassified_lot_requires_review_even_if_amount_is_zero():
    reasons = get_capital_gains_review_reasons({"has_unclassified_lot": True})
    assert "unclassified_capital_gain_lots" in reasons


def test_unmatched_quantity_requires_review():
    reasons = get_capital_gains_review_reasons({"unmatched_quantity": "2"})
    assert "unmatched_fifo_quantities" in reasons


def test_eligibility_review_requires_conditional_liability():
    reasons = get_capital_gains_review_reasons({"eligibility_review_required": True})
    assert "capital_gains_eligibility_review_required" in reasons


def test_clean_capital_gains_result_has_no_review_reasons():
    assert get_capital_gains_review_reasons({"unmatched_quantity": "0"}) == []
