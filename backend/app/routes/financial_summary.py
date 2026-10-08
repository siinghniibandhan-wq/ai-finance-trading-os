# ============================================================
# FINANCIAL OS
# FINANCIAL DATA ENGINE - SUMMARY
# ============================================================
#
# Version: 1.1
#
# Purpose:
#   Create one read-only financial snapshot from the
#   existing Financial OS data.
#
# Used later by:
#   Home
#   Plan
#   Tax
#   AI
#
# IMPORTANT:
#   This module does NOT modify:
#   - Transactions
#   - Investments
#   - Holdings
#   - P&L
#   - Market prices
#   - Database structure
# ============================================================

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, Transaction

from app.routes.holdings import (
    load_investments,
    load_transactions,
    build_holdings,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/financial-summary",
    tags=["Financial Data Engine"],
)


# ============================================================
# HELPER
# ============================================================

def to_decimal(value):
    """Safely convert a database value to Decimal."""

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

    Returns 0 when the denominator is zero.
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
# FINANCIAL SUMMARY
# ============================================================

@router.get("/")
def get_financial_summary(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a read-only financial snapshot.

    Example:

        GET /api/financial-summary/?user_id=1
    """

    # ========================================================
    # ACTIVE ACCOUNT BALANCE
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
    # TOTAL INCOME
    # ========================================================

    total_income = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
        )
        .scalar()
    )

    # ========================================================
    # TOTAL EXPENSE
    # ========================================================

    total_expense = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
        .scalar()
    )

    # ========================================================
    # NORMALIZE NUMBERS
    # ========================================================

    total_balance = to_decimal(
        total_balance
    )

    total_income = to_decimal(
        total_income
    )

    total_expense = to_decimal(
        total_expense
    )

    # ========================================================
    # NET CASH FLOW
    # ========================================================

    net_cash_flow = (
        total_income
        - total_expense
    )

    # ========================================================
    # SAVINGS RATE
    # ========================================================
    #
    # Formula:
    #
    #   Net Cash Flow / Income × 100
    #
    # If income is zero, savings rate = 0.
    #
    # ========================================================

    savings_rate = calculate_percentage(
        net_cash_flow,
        total_income,
    )

    # ========================================================
    # LOAD EXISTING INVESTMENT DATA
    # ========================================================

    investments = load_investments(
        db,
        user_id,
    )

    investment_transactions = load_transactions(
        db,
        user_id,
    )

    holdings = build_holdings(
        investments,
        investment_transactions,
    )

    # ========================================================
    # INVESTMENT TOTALS
    # ========================================================

    investment_cost_basis = sum(
        (
            to_decimal(
                holding.get(
                    "cost_basis",
                    0,
                )
            )
            for holding in holdings
        ),
        Decimal("0"),
    )

    investment_current_value = sum(
        (
            to_decimal(
                holding.get(
                    "current_value",
                    0,
                )
            )
            for holding in holdings
        ),
        Decimal("0"),
    )

    realised_gain_loss = sum(
        (
            to_decimal(
                holding.get(
                    "realised_gain_loss",
                    0,
                )
            )
            for holding in holdings
        ),
        Decimal("0"),
    )

    unrealised_gain_loss = sum(
        (
            to_decimal(
                holding.get(
                    "unrealised_gain_loss",
                    0,
                )
            )
            for holding in holdings
        ),
        Decimal("0"),
    )

    total_gain_loss = (
        realised_gain_loss
        + unrealised_gain_loss
    )

    # ========================================================
    # INVESTMENT RETURN
    # ========================================================
    #
    # Formula:
    #
    #   Total P&L / Cost Basis × 100
    #
    # This is a simple portfolio-level return indicator.
    #
    # It is NOT a time-weighted or XIRR return.
    #
    # ========================================================

    investment_return = calculate_percentage(
        total_gain_loss,
        investment_cost_basis,
    )

    # ========================================================
    # NET WORTH
    # ========================================================
    #
    # Current version:
    #
    #   Active account balances
    #   +
    #   Current investment value
    #
    # Future versions can add:
    #   Property
    #   Vehicles
    #   Other assets
    #   Loans
    #   Credit liabilities
    #
    # ========================================================

    net_worth = (
        total_balance
        + investment_current_value
    )

    # ========================================================
    # RETURN FINANCIAL SNAPSHOT
    # ========================================================

    return {
        "status": "success",

        "user_id": user_id,

        "engine": {
            "name": "Financial Data Engine",
            "version": "1.1",
            "read_only": True,
        },

        "cash": {
            "account_count": account_count,
            "total_balance": total_balance,
        },

        "cash_flow": {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_cash_flow": net_cash_flow,
            "savings_rate_percent": savings_rate,
        },

        "investments": {
            "holding_count": len(holdings),
            "total_cost_basis": investment_cost_basis,
            "current_value": investment_current_value,
            "realised_gain_loss": realised_gain_loss,
            "unrealised_gain_loss": unrealised_gain_loss,
            "total_gain_loss": total_gain_loss,
            "return_percent": investment_return,
        },

        "net_worth": {
            "total": net_worth,
        },
    }
