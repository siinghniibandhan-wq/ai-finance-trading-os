# ============================================================
# FINANCIAL OS
# FINANCIAL PLANNING ENGINE
# ============================================================
#
# Version: 1.0
#
# Purpose:
#   Provide a read-only financial planning snapshot using
#   existing Financial OS account and transaction data.
#
# Current planning metrics:
#   1. Current cash
#   2. Monthly income
#   3. Monthly expenses
#   4. Monthly savings
#   5. Savings rate
#   6. Emergency fund target
#   7. Emergency fund progress
#   8. Investment contribution capacity
#
# IMPORTANT:
#   This module does NOT modify:
#   - Transactions
#   - Accounts
#   - Categories
#   - Investments
#   - Holdings
#   - Database structure
#
# ============================================================


from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import (
    case,
    func,
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models import (
    Account,
    Transaction,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/financial-plan",
    tags=["Financial Planning"],
)


# ============================================================
# DECIMAL HELPER
# ============================================================

def to_decimal(value):
    """
    Safely convert database values to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# PERCENTAGE HELPER
# ============================================================

def calculate_percentage(
    numerator,
    denominator,
):
    """
    Safely calculate a percentage.

    Returns 0 when denominator is zero.
    """

    numerator = to_decimal(numerator)
    denominator = to_decimal(denominator)

    if denominator == 0:
        return Decimal("0")

    return (
        numerator
        / denominator
        * Decimal("100")
    )


# ============================================================
# FINANCIAL PLAN
# ============================================================

@router.get("/")
def get_financial_plan(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a read-only financial planning snapshot.

    Example:

        GET /api/financial-plan/?user_id=1

    Emergency fund assumption:

        6 months of monthly expenses.

    IMPORTANT:

        This is a planning indicator only.
        It does not create or modify any financial goal.
    """


    # ========================================================
    # CURRENT CASH
    # ========================================================

    total_balance = (
        db.query(
            func.coalesce(
                func.sum(Account.balance),
                0,
            )
        )
        .filter(
            Account.user_id == user_id,
            Account.is_active == True,
        )
        .scalar()
    )

    account_count = (
        db.query(
            func.count(Account.id)
        )
        .filter(
            Account.user_id == user_id,
            Account.is_active == True,
        )
        .scalar()
    )


    # ========================================================
    # TRANSACTION SUMMARY
    # ========================================================

    transaction_summary = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type
                            == "income",
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label(
