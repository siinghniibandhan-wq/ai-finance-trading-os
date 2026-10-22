"""Read-only Finance Diary API. No edit/delete endpoints are exposed."""
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import FinanceDiaryEntry, Transaction, Category, User
from app.routes.auth import get_current_user
from app.schemas import FinanceDiaryEntryResponse

router = APIRouter(prefix="/api/finance-diary", tags=["Finance Diary"])


@router.get("/daily-summary")
def finance_diary_daily_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-day income, expense and investment totals for the authenticated user.

    Transfers and refunds are deliberately excluded from income/expense totals.
    Investment activity is derived from immutable investment-creation diary snapshots.
    """
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date.")
    if (end_date - start_date).days > 366:
        raise HTTPException(status_code=422, detail="Select a date range of 366 days or less.")

    days = {}
    cursor = start_date
    while cursor <= end_date:
        days[cursor.isoformat()] = {
            "date": cursor.isoformat(),
            "total_income": Decimal("0.00"),
            "total_expense": Decimal("0.00"),
            "total_investment": Decimal("0.00"),
            "income_by_source": {},
            "expense_by_category": {},
            "investment_count": 0,
        }
        cursor += timedelta(days=1)

    transaction_rows = (
        db.query(Transaction, Category.name)
        .outerjoin(Category, (Category.id == Transaction.category_id) & (Category.user_id == current_user.id))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .all()
    )
    income_types = {"income", "interest", "dividend"}
    expense_types = {"expense", "tax", "loan_repayment"}
    for transaction, category_name in transaction_rows:
        day = days.get(transaction.transaction_date.isoformat())
        if day is None:
            continue
        kind = (transaction.transaction_type or "").strip().lower()
        amount = Decimal(str(transaction.amount or 0))
        if kind in income_types:
            day["total_income"] += amount
            source = (category_name or "Other income").strip() or "Other income"
            day["income_by_source"][source] = day["income_by_source"].get(source, Decimal("0.00")) + amount
        elif kind in expense_types:
            day["total_expense"] += amount
            category = (category_name or "Uncategorised").strip() or "Uncategorised"
            day["expense_by_category"][category] = day["expense_by_category"].get(category, Decimal("0.00")) + amount
        # Transfers, refunds and investment cash-ledger rows are not income/expense.

    investment_events = (
        db.query(FinanceDiaryEntry)
        .filter(
            FinanceDiaryEntry.user_id == current_user.id,
            FinanceDiaryEntry.entity_type.in_(["investment_transaction", "investment"]),
            FinanceDiaryEntry.event_type == "created",
            FinanceDiaryEntry.created_at >= datetime.combine(start_date, datetime.min.time()) - timedelta(hours=5, minutes=30),
            FinanceDiaryEntry.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()) - timedelta(hours=5, minutes=30),
        )
        .all()
    )
    for event in investment_events:
        day_key = (event.created_at + timedelta(hours=5, minutes=30)).date().isoformat() if event.created_at else None
        day = days.get(day_key)
        if day is None:
            continue
        try:
            snapshot = json.loads(event.snapshot_json or "{}")
            if event.entity_type == "investment_transaction":
                transaction_type = str(snapshot.get("transaction_type") or "").strip().lower()
                # Count purchase outflows as investments; sale proceeds are not new investment.
                if transaction_type not in {"buy", "purchase"}:
                    continue
                quantity = Decimal(str(snapshot.get("quantity") or 0))
                price = Decimal(str(snapshot.get("price") or 0))
                fees = Decimal(str(snapshot.get("fees") or 0))
            else:
                # New position creation also writes an initial BUY ledger row.
                # Avoid counting that same purchase twice.
                if snapshot.get("cash_deduction_handled_by_initial_buy_ledger"):
                    continue
                quantity = Decimal(str(snapshot.get("quantity") or 0))
                price = Decimal(str(snapshot.get("buy_price") or 0))
                fees = Decimal(str(snapshot.get("fees") or 0))
            invested = quantity * price + fees
        except (ValueError, TypeError, ArithmeticError):
            continue
        day["total_investment"] += invested
        day["investment_count"] += 1

    result = []
    for day in days.values():
        for key in ("total_income", "total_expense", "total_investment"):
            day[key] = str(day[key].quantize(Decimal("0.01")))
        day["income_by_source"] = {key: str(value.quantize(Decimal("0.01"))) for key, value in day["income_by_source"].items()}
        day["expense_by_category"] = {key: str(value.quantize(Decimal("0.01"))) for key, value in day["expense_by_category"].items()}
        result.append(day)
    return result


@router.get("/", response_model=list[FinanceDiaryEntryResponse])
def list_finance_diary(
    search: str | None = None,
    event_type: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Repair legacy/missing diary events for already-saved transactions.
    # A transaction may exist even if an older backend version did not write its
    # Finance Diary event. Reconciliation is user-scoped and idempotent.
    saved_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type != "transfer",
        )
        .all()
    )
    transaction_ids = {str(row.id) for row in saved_transactions}
    existing_created_ids = {
        value
        for (value,) in db.query(FinanceDiaryEntry.entity_id)
        .filter(
            FinanceDiaryEntry.user_id == current_user.id,
            FinanceDiaryEntry.entity_type == "transaction",
            FinanceDiaryEntry.event_type == "created",
            FinanceDiaryEntry.entity_id.isnot(None),
        )
        .all()
        if value is not None
    }
    missing_entries = []
    for transaction in saved_transactions:
        if str(transaction.id) in existing_created_ids:
            continue
        snapshot = {
            "id": transaction.id,
            "account_id": transaction.account_id,
            "category_id": transaction.category_id,
            "transaction_type": transaction.transaction_type,
            "amount": transaction.amount,
            "description": transaction.description,
            "transaction_date": transaction.transaction_date,
            "reference": transaction.reference,
            "reconciled_from_saved_transaction": True,
        }
        missing_entries.append(FinanceDiaryEntry(
            user_id=current_user.id,
            event_type="created",
            entity_type="transaction",
            entity_id=str(transaction.id),
            description=f"Transaction recovered in Finance Diary: {transaction.transaction_type} {transaction.amount}",
            snapshot_json=json.dumps(snapshot, default=str, sort_keys=True),
        ))
    if missing_entries:
        db.add_all(missing_entries)
        db.commit()

    # Finance Diary remains user-scoped; client cannot choose another user.
    query = db.query(FinanceDiaryEntry).filter(FinanceDiaryEntry.user_id == current_user.id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            FinanceDiaryEntry.description.ilike(pattern)
            | FinanceDiaryEntry.entity_type.ilike(pattern)
            | FinanceDiaryEntry.entity_id.ilike(pattern)
        )
    if event_type:
        query = query.filter(FinanceDiaryEntry.event_type == event_type)
    return query.order_by(FinanceDiaryEntry.created_at.desc(), FinanceDiaryEntry.id.desc()).offset(offset).limit(limit).all()
