# ============================================================
# FINANCIAL DASHBOARD API
# ============================================================

from decimal import Decimal
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id
from app.models import User, Account, Transaction, Category, Budget, LoanMovement


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# INCOME NORMALIZATION
# Loan principal is not earned income. For a linked recovery,
# only interest and fees are included in dashboard income.
# ============================================================

def _dashboard_income_amount(transaction, movements_by_transaction):
    transaction_type = (transaction.transaction_type or "").strip().lower()
    if transaction_type != "income":
        return Decimal("0")

    category_name = (
        (transaction.category.name or "").strip().lower()
        if transaction.category else ""
    )
    if category_name == "loan disbursement":
        return Decimal("0")

    movement = movements_by_transaction.get(transaction.id)
    if movement and (movement.movement_type or "").strip().lower() == "recovery":
        return (
            Decimal(str(movement.interest_amount or 0))
            + Decimal(str(movement.fee_amount or 0))
        )

    return Decimal(str(transaction.amount or 0))


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get("/summary", dependencies=[Depends(require_matching_user_id)])
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
            func.lower(Account.account_type).notin_([
                "loan", "loan_account", "personal_loan", "home_loan", "term_loan",
                "credit_card", "creditcard", "credit_card_account", "credit_line", "creditline", "credit line",
                "credit_line_account", "cash_credit", "cash_credit_account", "overdraft", "od", "payable", "receivable",
            ]),
        )
        .scalar()
    )

    # --------------------------------------------------------
    # Loan movements are used to exclude recovered principal
    # from income while retaining recovery interest/fees.
    # --------------------------------------------------------
    loan_movements = (
        db.query(LoanMovement)
        .filter(LoanMovement.user_id == user_id)
        .all()
    )
    movements_by_transaction = {
        movement.transaction_id: movement for movement in loan_movements
    }

    # --------------------------------------------------------
    # Total income (excluding loan principal)
    # --------------------------------------------------------
    income_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
        )
        .all()
    )
    total_income = sum(
        (_dashboard_income_amount(tx, movements_by_transaction) for tx in income_transactions),
        Decimal("0"),
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
        income_amount = _dashboard_income_amount(transaction, movements_by_transaction)
        if income_amount > 0:
            monthly_map[key]["income"] += float(income_amount)
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
    # Rolling 90-day averages for dashboard savings metrics
    # --------------------------------------------------------
    ninety_days_ago = today - timedelta(days=89)
    rolling_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= ninety_days_ago,
            Transaction.transaction_date <= today,
        )
        .all()
    )
    rolling_income = Decimal("0")
    rolling_expense = Decimal("0")
    for transaction in rolling_transactions:
        amount = Decimal(str(transaction.amount or 0))
        kind = (transaction.transaction_type or "").lower()
        income_amount = _dashboard_income_amount(transaction, movements_by_transaction)
        if income_amount > 0:
            rolling_income += income_amount
        elif kind == "expense":
            rolling_expense += amount
    # Use a 3-month estimate for consistency with the planning screen.
    average_monthly_income = rolling_income / Decimal("3")
    average_monthly_expense = rolling_expense / Decimal("3")
    estimated_monthly_savings = average_monthly_income - average_monthly_expense
    savings_rate = (
        (estimated_monthly_savings / average_monthly_income * Decimal("100"))
        if average_monthly_income > 0 else Decimal("0")
    )

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
            "average_monthly_income": round(float(average_monthly_income), 2),
            "average_monthly_expense": round(float(average_monthly_expense), 2),
            "estimated_monthly_savings": round(float(estimated_monthly_savings), 2),
            "savings_rate": round(float(savings_rate), 2),
            "rolling_period_days": 90,
        },
        "monthly_trend": list(monthly_map.values()),
        "expense_breakdown": expense_breakdown,
        "alerts": budget_alerts,
        "recent_transactions": recent_data,
    }
