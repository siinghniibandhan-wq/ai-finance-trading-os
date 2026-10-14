"""Safety rules that keep non-income money out of taxable income.

Pure functions only (no database or web imports) so they are easy to test.

Rules:
  * Refunds, reversals, reimbursements, chargebacks, transfers and loan
    principal are NOT income, even if someone saved them with type "income".
  * Excluded rows are never silently dropped: callers get a reason for each.
  * Exact duplicates (same account, date, type, amount AND the same non-empty
    reference) are counted once. Look-alikes without a reference are only
    flagged for review, because two genuine receipts can share an amount.
"""
import re
from decimal import Decimal

NON_INCOME_CATEGORY_TERMS = (
    "refund", "reversal", "reimbursement", "chargeback", "transfer",
    "loan disbursement", "loan principal", "borrowing",
)

_NON_INCOME_DESCRIPTION = re.compile(
    r"\b(refund(ed)?|reversal|reversed|reimburse(ment|d)?|chargeback"
    r"|(self|own[- ]account|inter[- ]?account)\s+transfer"
    r"|transfer\s+(to|from))\b",
    re.IGNORECASE,
)


def non_income_reason(category_path, description):
    """Return why a saved "income" row is not taxable income, or None."""
    category = str(category_path or "").strip().lower()
    for term in NON_INCOME_CATEGORY_TERMS:
        if term in category:
            return f"category looks like {term}, not earned income"
    match = _NON_INCOME_DESCRIPTION.search(str(description or ""))
    if match:
        return f"description mentions '{match.group(0).lower()}', not earned income"
    return None


def _key(row):
    return (
        row.account_id,
        row.transaction_date,
        str(row.transaction_type or "").strip().lower(),
        Decimal(str(row.amount)),
    )


def find_duplicates(rows):
    """Return (exact_duplicate_ids, possible_duplicate_ids).

    exact: same key and the same non-empty reference -> later rows are excluded.
    possible: same key, no reference -> flagged only, still counted.
    """
    exact, possible = set(), set()
    seen_with_ref, seen_no_ref = {}, {}
    for row in sorted(rows, key=lambda r: r.id):
        reference = str(getattr(row, "reference", "") or "").strip().lower()
        key = _key(row)
        if reference:
            full_key = key + (reference,)
            if full_key in seen_with_ref:
                exact.add(row.id)
            else:
                seen_with_ref[full_key] = row.id
        else:
            if key in seen_no_ref:
                possible.add(row.id)
                possible.add(seen_no_ref[key])
            else:
                seen_no_ref[key] = row.id
    return exact, possible
