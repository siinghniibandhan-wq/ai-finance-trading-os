"""Rules for the owner's verify step on deduction claims and tax credits."""
from app.routes.deductions_exempt_income import claim_verification_problem
from app.routes.final_tax_liability import credit_verification_problem


def test_claim_without_evidence_cannot_be_verified():
    assert claim_verification_problem(None)
    assert claim_verification_problem("")
    assert claim_verification_problem("   ")


def test_claim_with_evidence_can_be_verified():
    assert claim_verification_problem("LIC policy 123456") is None


def test_credit_without_reference_cannot_be_verified():
    assert credit_verification_problem(None, [])
    assert credit_verification_problem("  ", ["A"])


def test_credit_with_new_reference_can_be_verified():
    assert credit_verification_problem("26AS-TDS-2026", ["ADV-1", None]) is None


def test_credit_reusing_a_verified_reference_is_refused_ignoring_case_and_spaces():
    assert credit_verification_problem(" challan-77 ", ["CHALLAN-77"])
    assert credit_verification_problem("challan-77", ["Challan-77 "])
