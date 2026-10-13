"""Regression tests for read-only tax classification of Money transactions."""
import os
import unittest
from decimal import Decimal
from datetime import date

# The application database module requires this variable at import time.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/financialos_tax_tests.db")

from app.routes.itr_ready_tax_report import (  # noqa: E402
    apply_verified_annual_salary_record,
    load_other_income,
)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class FakeDB:
    def execute(self, _query, _params):
        return FakeResult([
            {
                "id": 1, "transaction_type": "income", "amount": "50000",
                "transaction_date": date(2026, 4, 5), "description": "Monthly salary credit",
                "category_name": "General Income", "category_description": "",
            },
            {
                "id": 2, "transaction_type": "income", "amount": "200000",
                "transaction_date": date(2026, 4, 6), "description": "Home loan disbursement",
                "category_name": "Income", "category_description": "",
            },
            {
                "id": 3, "transaction_type": "interest", "amount": "1200",
                "transaction_date": date(2026, 4, 7), "description": "Salary adjustment",
                "category_name": "Bank Interest", "category_description": "",
            },
            {
                "id": 4, "transaction_type": "dividend", "amount": "300",
                "transaction_date": date(2026, 4, 8), "description": "Quarterly dividend",
                "category_name": "Dividend", "category_description": "",
            },
        ])


class TaxIncomeClassificationTests(unittest.TestCase):
    def test_salary_keyword_without_gross_metadata_is_flagged_not_taxed_as_net(self):
        result = load_other_income(FakeDB(), 1, date(2026, 4, 1), date(2027, 3, 31))
        # The transaction is a net receipt; tax must use saved gross salary
        # metadata rather than silently treating the bank credit as gross pay.
        self.assertEqual(result["salary"], 0)
        salary_reviews = [
            item for item in result["classification_review"]
            if item["transaction_id"] == 1
        ]
        self.assertEqual(len(salary_reviews), 1)
        self.assertIn("Gross salary metadata", salary_reviews[0]["reason"])


    def test_verified_annual_salary_record_is_authoritative_and_not_double_counted(self):
        result = load_other_income(FakeDB(), 1, date(2026, 4, 1), date(2027, 3, 31))

        class SalaryRecord:
            gross_salary = "720000.00"

        merged = apply_verified_annual_salary_record(result, SalaryRecord())
        self.assertEqual(merged["salary"], Decimal("720000.00"))
        self.assertEqual(merged["total"], Decimal("721500.00"))
        salary_details = [item for item in merged["details"] if item.get("tax_head") == "salary"]
        self.assertEqual(len(salary_details), 1)
        self.assertEqual(salary_details[0]["classification_source"], "verified_annual_salary_record")
        self.assertFalse(any("Gross salary metadata" in item.get("reason", "") for item in merged["classification_review"]))

    def test_loan_disbursement_is_excluded_from_income(self):
        result = load_other_income(FakeDB(), 1, date(2026, 4, 1), date(2027, 3, 31))
        self.assertEqual(len(result["excluded_loan_proceeds"]), 1)
        self.assertEqual(result["excluded_loan_proceeds"][0]["transaction_id"], 2)
        self.assertNotEqual(result["total"], 251500)

    def test_explicit_interest_type_conflict_is_flagged(self):
        result = load_other_income(FakeDB(), 1, date(2026, 4, 1), date(2027, 3, 31))
        self.assertEqual(result["interest"], 1200)
        conflict_reviews = [
            item for item in result["classification_review"]
            if item["transaction_id"] == 3
        ]
        self.assertEqual(len(conflict_reviews), 1)
        self.assertEqual(conflict_reviews[0]["suggested_head"], "salary")

    def test_dividend_is_separately_classified(self):
        result = load_other_income(FakeDB(), 1, date(2026, 4, 1), date(2027, 3, 31))
        self.assertEqual(result["dividend"], 300)
        self.assertEqual(result["other_sources_total"], 1500)


if __name__ == "__main__":
    unittest.main()
