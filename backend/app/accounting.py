"""Persistent double-entry posting for Money transactions.

This service records a balanced journal projection of the existing transaction
record. It does not alter account balances or tax results.
"""
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import (
    Account, Category, ChartOfAccount, JournalEntry, JournalLine, Transaction,
)

DEFAULT_ACCOUNTS = [
    ("1000", "Assets", "Asset", None, None),
    ("1010", "Cash", "Asset", "1000", None),
    ("1020", "Bank Accounts", "Asset", "1000", None),
    ("1100", "Receivables", "Asset", "1000", None),
    ("1110", "Customer Receivables", "Asset", "1100", None),
    ("1120", "Other Receivables", "Asset", "1100", None),
    ("1200", "Investments", "Asset", "1000", None),
    ("1210", "Mutual Fund Investments", "Asset", "1200", "capital_gains"),
    ("1220", "Stocks", "Asset", "1200", "capital_gains"),
    ("1230", "ETFs", "Asset", "1200", "capital_gains"),
    ("1240", "Bonds", "Asset", "1200", "capital_gains"),
    ("2000", "Liabilities", "Liability", None, None),
    ("2010", "Payables", "Liability", "2000", None),
    ("2020", "Credit Card Payable", "Liability", "2000", None),
    ("2030", "Loans Payable", "Liability", "2000", None),
    ("3000", "Equity", "Equity", None, None),
    ("4000", "Income", "Income", None, None),
    ("4010", "Salary Income", "Income", "4000", "salary"),
    ("4020", "Business and Professional Income", "Income", "4000", "business_profession"),
    ("4030", "Rental Income", "Income", "4000", "house_property"),
    ("4040", "Interest Income", "Income", "4000", "other_sources"),
    ("4050", "Dividend Income", "Income", "4000", "other_sources"),
    ("4060", "Other Income — Review Required", "Income", "4000", "review_required"),
    ("5000", "Expenses", "Expense", None, None),
    ("5010", "Living Expenses", "Expense", "5000", None),
    ("5020", "Business Expenses", "Expense", "5000", "business_expense_review"),
    ("5030", "Property Expenses", "Expense", "5000", "house_property_expense_review"),
    ("5040", "Loan Interest", "Expense", "5000", "interest_purpose_review"),
    ("5050", "Taxes Paid", "Expense", "5000", "tax_payment"),
]

def _ensure_default_accounts(db: Session, user_id: int) -> dict[str, ChartOfAccount]:
    """Create missing catalogue rows inside the caller's transaction (no commit)."""
    rows = {r.code: r for r in db.query(ChartOfAccount).filter_by(user_id=user_id).all()}
    for code, name, kind, parent_code, tax_key in DEFAULT_ACCOUNTS:
        row = rows.get(code)
        if row is None:
            row = ChartOfAccount(
                user_id=user_id, code=code, name=name, account_type=kind,
                is_system=True, is_enabled=True, tax_mapping_key=tax_key,
            )
            db.add(row)
            db.flush()
            rows[code] = row
        if parent_code and row.parent_id is None:
            parent = rows.get(parent_code)
            if parent:
                row.parent_id = parent.id
    return rows

def _real_account_code(account: Account | None) -> str:
    if account is None:
        return "1020"
    kind = (account.account_type or "").strip().lower().replace("-", "_").replace(" ", "_")
    name = (account.name or "").strip().lower()
    if "cash" in kind or name == "cash" or "wallet" in kind:
        return "1010"
    if "credit_card" in kind or "creditcard" in kind:
        return "2020"
    if "loan" in kind:
        return "2030"
    if "payable" in kind:
        return "2010"
    if "receivable" in kind:
        return "1120"
    if "mutual_fund" in kind or "mutual fund" in name:
        return "1210"
    if "etf" in kind or "etf" in name:
        return "1230"
    if "bond" in kind or "bond" in name:
        return "1240"
    if "stock" in kind or "equity" in kind or "share" in name:
        return "1220"
    if "investment" in kind or "broker" in kind:
        return "1200"
    return "1020"

def _counter_account_code(tx_type: str, category: Category | None) -> str:
    t = (tx_type or "").strip().lower()
    category_name = (category.name or "").strip().lower() if category else ""
    category_type = (category.category_type or "").strip().lower() if category else ""
    if "loan disbursement" in category_name:
        return "2030"
    if t in {"income", "interest", "dividend"}:
        if "salary" in category_name:
            return "4010"
        if any(word in category_name for word in ("business", "professional", "freelance", "gig")):
            return "4020"
        if any(word in category_name for word in ("rent", "rental")):
            return "4030"
        if "interest" in category_name:
            return "4040"
        if "dividend" in category_name:
            return "4050"
        return "4060"
    if t == "tax":
        return "5050"
    if t == "loan_repayment" or "loan interest" in category_name:
        return "5040"
    if category_type == "expense" and any(word in category_name for word in ("business", "professional", "office")):
        return "5020"
    if category_type == "expense" and any(word in category_name for word in ("property", "maintenance", "repairs")):
        return "5030"
    return "5010"

def sync_transaction_journal(db: Session, transaction: Transaction) -> JournalEntry:
    """Replace the journal projection for one transaction with two balanced lines."""
    old_entry_ids = [
        row[0] for row in db.query(JournalEntry.id).filter_by(
            user_id=transaction.user_id, transaction_id=transaction.id
        ).all()
    ]
    if old_entry_ids:
        db.query(JournalLine).filter(
            JournalLine.journal_entry_id.in_(old_entry_ids)
        ).delete(synchronize_session=False)
        db.query(JournalEntry).filter(
            JournalEntry.id.in_(old_entry_ids), JournalEntry.user_id == transaction.user_id
        ).delete(synchronize_session=False)
    account_rows = _ensure_default_accounts(db, transaction.user_id)
    amount = Decimal(str(transaction.amount)).quantize(Decimal("0.01"))
    if amount <= 0:
        raise ValueError("Journal amount must be greater than zero")

    source = db.query(Account).filter_by(
        id=transaction.account_id, user_id=transaction.user_id
    ).first()
    category = None
    if transaction.category_id is not None:
        category = db.query(Category).filter_by(
            id=transaction.category_id, user_id=transaction.user_id
        ).first()
    tx_type = (transaction.transaction_type or "").strip().lower()
    description = (transaction.description or transaction.transaction_type or "Transaction")[:255]
    entry = JournalEntry(
        user_id=transaction.user_id, transaction_id=transaction.id,
        entry_date=transaction.transaction_date, description=description,
    )
    db.add(entry)
    db.flush()

    def line(code: str, financial_account_id: int | None, debit=Decimal("0.00"), credit=Decimal("0.00"), order=1):
        db.add(JournalLine(
            journal_entry_id=entry.id, chart_of_account_id=account_rows[code].id,
            financial_account_id=financial_account_id, description=description,
            debit=debit, credit=credit, entry_order=order,
        ))

    if tx_type == "transfer":
        destination = db.query(Account).filter_by(
            id=transaction.transfer_to_account_id, user_id=transaction.user_id
        ).first()
        if destination is None:
            raise ValueError("Transfer destination account is missing or belongs to another user")
        # Transfer is a balance-sheet movement: destination debit, source credit.
        line(_real_account_code(destination), destination.id, debit=amount, order=1)
        line(_real_account_code(source), source.id, credit=amount, order=2)
    elif tx_type in {"income", "interest", "dividend", "refund"}:
        line(_real_account_code(source), source.id, debit=amount, order=1)
        contra_code = _counter_account_code(tx_type, category)
        line(contra_code, None, credit=amount, order=2)
    elif tx_type in {"expense", "withdrawal", "tax", "loan_repayment"}:
        contra_code = _counter_account_code(tx_type, category)
        line(contra_code, None, debit=amount, order=1)
        line(_real_account_code(source), source.id, credit=amount, order=2)
    else:
        # Do not silently invent accounting for an unknown transaction type.
        raise ValueError(f"Unsupported transaction type for ledger posting: {tx_type}")
    return entry
