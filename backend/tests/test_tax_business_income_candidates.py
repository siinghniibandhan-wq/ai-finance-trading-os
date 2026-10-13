from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routes.tax_business_income import (
    _financial_year_dates,
    _is_business_receipt_candidate,
)


class FakeQuery:
    def __init__(self, category):
        self.category = category

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.category


class FakeDB:
    def __init__(self, category=None):
        self.category = category

    def query(self, model):
        return FakeQuery(self.category)


def tx(kind="income", category_id=1, description="Consulting payment"):
    return SimpleNamespace(
        transaction_type=kind,
        category_id=category_id,
        description=description,
    )


def test_financial_year_bounds_are_inclusive_indian_fy():
    assert _financial_year_dates("2026-27") == (
        date(2026, 4, 1),
        date(2027, 3, 31),
    )


@pytest.mark.parametrize("year", ["2026-26", "2026-28", "bad", "1999-00"])
def test_invalid_financial_year_rejected(year):
    with pytest.raises(HTTPException) as exc:
        _financial_year_dates(year)
    assert exc.value.status_code == 400


@pytest.mark.parametrize(
    "category",
    ["Salary", "Salary & Wages", "Salaries", "Loan Disbursement", "Interest", "Dividend"],
)
def test_non_business_income_categories_are_not_candidates(category):
    assert not _is_business_receipt_candidate(
        FakeDB(SimpleNamespace(name=category)), tx()
    )


def test_gross_salary_metadata_is_not_candidate_even_with_generic_category():
    assert not _is_business_receipt_candidate(
        FakeDB(SimpleNamespace(name="Other Income")),
        tx(description="Gross salary: ₹50,000; net credit ₹45,000"),
    )


def test_only_income_transactions_can_be_receipt_candidates():
    assert not _is_business_receipt_candidate(
        FakeDB(SimpleNamespace(name="Consulting")), tx(kind="expense")
    )


@pytest.mark.parametrize(
    "category",
    ["Other Sources > Savings Interest", "Other Sources > Dividends", "Business/Profession > Salary"],
)
def test_hierarchical_tax_categories_are_excluded(category):
    assert not _is_business_receipt_candidate(
        FakeDB(SimpleNamespace(name=category)), tx()
    )


def test_unclassified_income_can_be_candidate_for_human_review():
    assert _is_business_receipt_candidate(
        FakeDB(SimpleNamespace(name="Business/Profession > Business Income")), tx()
    )
