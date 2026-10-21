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
        .outerjoin(Category, Category.id == Transaction.category_id)
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
            FinanceDiaryEntry.entity_type == "investment",
            FinanceDiaryEntry.event_type == "created",
            FinanceDiaryEntry.created_at >= datetime.combine(start_date, datetime.min.time()),
            FinanceDiaryEntry.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
        )
        .all()
    )
    for event in investment_events:
        day_key = event.created_at.date().isoformat() if event.created_at else None
        day = days.get(day_key)
        if day is None:
            continue
        try:
            snapshot = json.loads(event.snapshot_json or "{}")
            quantity = Decimal(str(snapshot.get("quantity") or 0))
            buy_price = Decimal(str(snapshot.get("buy_price") or 0))
            fees = Decimal(str(snapshot.get("fees") or 0))
            invested = quantity * buy_price + fees
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
