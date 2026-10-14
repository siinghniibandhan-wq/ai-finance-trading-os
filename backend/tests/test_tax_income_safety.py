import sys, os
from datetime import date
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.tax_income_safety import non_income_reason, find_duplicates


def row(i, amount=100, ref=None, account=1, day=1, kind="income"):
    return SimpleNamespace(id=i, account_id=account, transaction_date=date(2026, 5, day),
                           transaction_type=kind, amount=amount, reference=ref)


def test_refund_category_is_not_income():
    assert non_income_reason("Refund", "") is not None
    assert non_income_reason("Transfer", "") is not None
    assert non_income_reason("Loan Disbursement", "") is not None


def test_refund_description_is_not_income():
    assert non_income_reason("Other", "Amazon refund for order") is not None
    assert non_income_reason("Other", "Self transfer from savings") is not None
    assert non_income_reason("Other", "Reimbursement from office") is not None


def test_real_income_is_kept():
    assert non_income_reason("Freelance", "Website design payment") is None
    assert non_income_reason("Savings Interest", "Interest credited") is None
    assert non_income_reason(None, None) is None


def test_exact_duplicate_with_reference_counted_once():
    exact, possible = find_duplicates([row(1, ref="UTR1"), row(2, ref="utr1")])
    assert exact == {2} and possible == set()


def test_same_amount_without_reference_only_flagged():
    exact, possible = find_duplicates([row(1), row(2)])
    assert exact == set() and possible == {1, 2}


def test_different_day_or_amount_is_not_duplicate():
    exact, possible = find_duplicates([row(1, ref="A"), row(2, ref="A", day=2), row(3, amount=5, ref="A")])
    assert exact == set() and possible == set()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("passed", name)
