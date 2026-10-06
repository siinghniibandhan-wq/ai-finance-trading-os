# ============================================================
# FINANCIAL DASHBOARD API
# ============================================================

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, Account, Transaction


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
            Account.active == True,
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

        "recent_transactions": recent_data,
    }
