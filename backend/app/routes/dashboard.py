# ============================================================
# FINANCIAL DASHBOARD API
# ============================================================

from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, Account, Transaction, Category, Budget


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get("/summary")
def get_dashboard_summary(
    user_id: int,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Check user
    # --------------------------------------------------------
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # --------------------------------------------------------
    # Total account balance
    # --------------------------------------------------------
    total_balance = (
        db.query(func.coalesce(func.sum(Account.balance), 0))
        .filter(
            Account.user_id == user_id,
            Account.is_active == True,
        )
        .scalar()
    )

    # --------------------------------------------------------
    # Total income
    # --------------------------------------------------------
    total_income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
        )
        .scalar()
    )

    # --------------------------------------------------------
    # Total expenses
    # --------------------------------------------------------
    total_expense = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
        .scalar()
    )

    # --------------------------------------------------------
    # Net cash flow
    # --------------------------------------------------------
    net_cash_flow = (
        Decimal(str(total_income))
        - Decimal(str(total_expense))
    )

    # --------------------------------------------------------
    # Account count
    # --------------------------------------------------------
    account_count = (
        db.query(func.count(Account.id))
        .filter(
            Account.user_id == user_id,
            Account.is_active == True,
        )
        .scalar()
    )

    # --------------------------------------------------------
    # Transaction count
    # --------------------------------------------------------
    transaction_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == user_id,
        )
        .scalar()
    )

    # --------------------------------------------------------
    # Recent transactions
    # --------------------------------------------------------
    recent_transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .limit(10)
        .all()
    )

    recent_data = []

    for transaction in recent_transactions:
        recent_data.append(
            {
                "id": transaction.id,
                "account_id": transaction.account_id,
                "category_id": transaction.category_id,
                "transaction_type": transaction.transaction_type,
                "amount": float(transaction.amount),
                "description": transaction.description,
                "transaction_date": transaction.transaction_date,
                "reference": transaction.reference,
            }
        )

    # --------------------------------------------------------
    # Six-month cash-flow trend (based on actual dated records)
    # --------------------------------------------------------
    today = date.today()
    month_starts = []
    year, month = today.year, today.month
    for _ in range(5):
        month = 1 if month == 1 else month
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
    # Build the last six calendar months in chronological order.
    year, month = today.year, today.month
    for _ in range(5):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    start_year, start_month = year, month
    for offset in range(6):
        m = start_month + offset
        y = start_year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        month_starts.append((y, m))

    first_y, first_m = month_starts[0]
    trend_start = date(first_y, first_m, 1)
    trend_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= trend_start,
            Transaction.transaction_date <= today,
        )
        .all()
    )
    monthly_map = {}
    for y, m in month_starts:
        key = f"{y:04d}-{m:02d}"
        monthly_map[key] = {"month": key, "income": 0.0, "expenses": 0.0, "net": 0.0}
    for transaction in trend_transactions:
        key = transaction.transaction_date.strftime("%Y-%m")
        if key not in monthly_map:
            continue
        amount = float(transaction.amount or 0)
        if (transaction.transaction_type or "").lower() == "income":
            monthly_map[key]["income"] += amount
        elif (transaction.transaction_type or "").lower() == "expense":
            monthly_map[key]["expenses"] += amount
    for item in monthly_map.values():
        item["net"] = round(item["income"] - item["expenses"], 2)
        item["income"] = round(item["income"], 2)
        item["expenses"] = round(item["expenses"], 2)

    # --------------------------------------------------------
    # Current-month expense mix by category
    # --------------------------------------------------------
    month_start = date(today.year, today.month, 1)
    expense_rows = (
        db.query(Category.name, func.coalesce(func.sum(Transaction.amount), 0))
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= today,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(6)
        .all()
    )
    expense_breakdown = [
        {"category": name or "Uncategorised", "amount": round(float(amount or 0), 2)}
        for name, amount in expense_rows
    ]

    # --------------------------------------------------------
    # Budget alerts for the current month. Budget model is user-scoped.
    # --------------------------------------------------------
    current_month_key = today.strftime("%Y-%m")
    budgets = (
        db.query(Budget, Category.name)
        .outerjoin(Category, Budget.category_id == Category.id)
        .filter(Budget.user_id == user_id, Budget.month == current_month_key)
        .all()
    )
    budget_alerts = []
    for budget, category_name in budgets:
        spent = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.transaction_type == "expense",
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= today,
            )
            .scalar()
        )
        limit_amount = float(budget.amount or 0)
        spent_amount = float(spent or 0)
        percent = (spent_amount / limit_amount * 100) if limit_amount > 0 else 0
        if percent >= 80:
            budget_alerts.append({
                "type": "budget",
                "severity": "critical" if percent >= 100 else "warning",
                "title": "Budget limit reached" if percent >= 100 else "Budget nearly exhausted",
                "message": f"{category_name or 'Category'}: {percent:.0f}% used this month.",
                "amount": round(spent_amount, 2),
                "limit": round(limit_amount, 2),
                "percent": round(percent, 1),
            })

    # --------------------------------------------------------
    # Final dashboard response
    # --------------------------------------------------------
    return {
        "user_id": user_id,
        "currency": user.currency,
        "summary": {
            "total_balance": float(total_balance),
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "net_cash_flow": float(net_cash_flow),
            "account_count": account_count,
            "transaction_count": transaction_count,
        },
        "monthly_trend": list(monthly_map.values()),
        "expense_breakdown": expense_breakdown,
        "alerts": budget_alerts,
        "recent_transactions": recent_data,
    }
