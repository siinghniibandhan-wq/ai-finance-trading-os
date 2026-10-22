"""Read-only views and authenticated backfill for persisted accounting journals."""
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.auth import get_current_user
from app.models import User, Transaction, JournalEntry, JournalLine, ChartOfAccount, Account
from app.accounting import sync_transaction_journal

router = APIRouter(prefix="/api/ledger", tags=["Ledger"])

@router.get("/")
def list_ledger_entries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(JournalEntry, JournalLine, ChartOfAccount, Account)
        .join(JournalLine, JournalLine.journal_entry_id == JournalEntry.id)
        .join(ChartOfAccount, ChartOfAccount.id == JournalLine.chart_of_account_id)
        .outerjoin(Account, Account.id == JournalLine.financial_account_id)
        .filter(JournalEntry.user_id == current_user.id, ChartOfAccount.user_id == current_user.id)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc(), JournalLine.entry_order.asc())
        .all()
    )
    entries = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    for header, line, coa, financial_account in rows:
        debit = Decimal(str(line.debit or 0))
        credit = Decimal(str(line.credit or 0))
        total_debit += debit
        total_credit += credit
        entries.append({
            "id": line.id,
            "journal_entry_id": header.id,
            "transaction_id": header.transaction_id,
            "date": header.entry_date,
            "description": line.description or header.description,
            "account_code": coa.code,
            "account_name": coa.name,
            "financial_account_id": line.financial_account_id,
            "financial_account_name": financial_account.name if financial_account else None,
            "debit": debit,
            "credit": credit,
        })
    return {
        "entries": entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": total_debit == total_credit,
    }

@router.post("/backfill")
def backfill_ledger(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Post historical source transactions that do not yet have journal entries.

    Each row uses a savepoint so one unsupported legacy type does not prevent
    other valid transactions from being backfilled.
    """
    existing_ids = {
        row[0] for row in db.query(JournalEntry.transaction_id)
        .filter(JournalEntry.user_id == current_user.id).all()
    }
    source_rows = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.id.asc()).all()
    posted = 0
    skipped = []
    for transaction in source_rows:
        if transaction.id in existing_ids:
            continue
        try:
            with db.begin_nested():
                sync_transaction_journal(db, transaction)
            posted += 1
        except Exception as exc:
            skipped.append({"transaction_id": transaction.id, "reason": str(exc)[:240]})
    db.commit()
    return {"posted": posted, "skipped_count": len(skipped), "skipped": skipped}
