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


# ============================================================
# DATE AND FINANCIAL CALCULATION IMPORTS
# ============================================================

from datetime import date, timedelta
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
from app.routes.ownership import require_matching_user_id

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

@router.get("/", dependencies=[Depends(require_matching_user_id)])
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
            ~func.lower(Account.account_type).in_([
                "loan", "loan_account", "personal_loan", "home_loan", "term_loan",
                "credit_card", "creditcard", "credit_card_account", "credit_line", "creditline", "credit line",
                "credit_line_account", "cash_credit", "cash_credit_account", "overdraft", "od", "payable", "receivable",
            ]),
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
            ~func.lower(Account.account_type).in_([
                "loan", "loan_account", "personal_loan", "home_loan", "term_loan",
                "credit_card", "creditcard", "credit_card_account", "credit_line", "creditline", "credit line",
                "credit_line_account", "cash_credit", "cash_credit_account", "overdraft", "od", "payable", "receivable",
            ]),
        )
        .scalar()
    )


    # ========================================================
    # TRANSACTION SUMMARY - LAST 90 DAYS
    # ========================================================
    #
    # IMPORTANT:
    # We use the last 90 calendar days for financial planning.
    #
    # Monthly planning figures will be calculated by dividing
    # the 90-day totals by 3.
    #
    # Only income and expense transactions are included,
    # preserving the existing transaction classifications.
    #
    # No transactions or database records are modified.
    #
    # ========================================================

    planning_end_date = date.today()

    planning_start_date = (
        planning_end_date - timedelta(days=89)
    )

    transaction_summary = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type == "income",
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("income"),

            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type == "expense",
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("expense"),

            func.count(
                Transaction.id
            ).label("transaction_count"),
        )
        .filter(
            Transaction.user_id == user_id,

            Transaction.transaction_date >= planning_start_date,

            Transaction.transaction_date <= planning_end_date,
        )
        .one()
    )

    # ========================================================
    # NORMALIZE 90-DAY TOTALS
    # ========================================================

    total_balance = to_decimal(
        total_balance
    )

    total_income = to_decimal(
        transaction_summary.income
    )

    total_expense = to_decimal(
        transaction_summary.expense
    )

    transaction_count = (
        transaction_summary.transaction_count or 0
    )

    # ========================================================
    # MONTHLY PLANNING BASE
    # ========================================================
    #
    # Calculate average monthly figures using the last
    # 90 calendar days of recorded transactions.
    #
    # The 90-day period is treated as three months for
    # planning purposes.
    #
    # ========================================================

    planning_months = Decimal("3")

    monthly_income = (
        total_income / planning_months
    )

    monthly_expense = (
        total_expense / planning_months
    )

    monthly_savings = (
        monthly_income
        - monthly_expense
    )


    # ========================================================
    # SAVINGS RATE
    # ========================================================

    savings_rate = calculate_percentage(
        monthly_savings,
        monthly_income,
    )



    # ========================================================
    # EMERGENCY FUND
    # ========================================================
    #
    # Calculate the emergency fund using eligible bank
    # and cash accounts only.
    #
    # Investment accounts and credit cards are excluded.
    # Other account types require separate classification.
    #
    # ========================================================

    emergency_fund_months = Decimal("6")

    # --------------------------------------------------------
    # Calculate the emergency fund target.
    # --------------------------------------------------------

    emergency_fund_target = (
        monthly_expense
        * emergency_fund_months
    )

    # --------------------------------------------------------
    # Calculate eligible emergency cash.
    # --------------------------------------------------------

    emergency_fund_current = (
        db.query(
            func.coalesce(
                func.sum(Account.balance),
                0,
            )
        )
        .filter(
            Account.user_id == user_id,
            Account.is_active == True,
            Account.account_type.in_([
                "bank",
                "cash",
            ]),
        )
        .scalar()
    )

    emergency_fund_current = to_decimal(
        emergency_fund_current
    )

    # ========================================================
    # EMERGENCY FUND PROGRESS
    # ========================================================

    emergency_fund_progress = calculate_percentage(
        emergency_fund_current,
        emergency_fund_target,
    )

    if emergency_fund_progress > Decimal("100"):
        emergency_fund_progress = Decimal("100")


    # ========================================================
    # EMERGENCY FUND REMAINING
    # ========================================================

    emergency_fund_remaining = (
        emergency_fund_target
        - emergency_fund_current
    )

    if emergency_fund_remaining < Decimal("0"):
        emergency_fund_remaining = Decimal("0")


    # ========================================================
    # INVESTMENT CONTRIBUTION CAPACITY
    # ========================================================

    investment_contribution_capacity = (
        monthly_savings
    )

    if investment_contribution_capacity < Decimal("0"):
        investment_contribution_capacity = Decimal("0")


    # ========================================================
    # FINANCIAL POSITION
    # ========================================================

    if monthly_income == 0:

        financial_position = "no_income_data"

    elif monthly_savings < 0:

        financial_position = "negative_cash_flow"

    elif monthly_savings == 0:

        financial_position = "break_even"

    else:

        financial_position = "positive_cash_flow"


    # ========================================================
    # RETURN FINANCIAL PLAN
    # ========================================================

    return {
        "status": "success",

        "user_id": user_id,

        # ----------------------------------------------------
        # PLANNING ENGINE VERSION AND CALCULATION PERIOD
        # ----------------------------------------------------

        "planning_engine": {
            "name": "Financial Planning Engine",
            "version": "1.1",
            "read_only": True,
            "calculation_basis": "rolling_90_day_average",
            "period_start": planning_start_date.isoformat(),
            "period_end": planning_end_date.isoformat(),
            "period_days": 90,
        },

        "cash": {
            "account_count": account_count,
            "current_balance": total_balance,
        },

        "monthly_cash_flow": {
            "income": monthly_income,
            "expense": monthly_expense,
            "savings": monthly_savings,
            "savings_rate_percent": savings_rate,
        },

        "emergency_fund": {
            "target_months": emergency_fund_months,
            "target_amount": emergency_fund_target,
            "current_amount": emergency_fund_current,
            "remaining_amount": emergency_fund_remaining,
            "progress_percent": emergency_fund_progress,
        },

        "investment_planning": {
            "monthly_contribution_capacity": (
                investment_contribution_capacity
            ),
        },

        "financial_position": {
            "status": financial_position,
            "transaction_count": transaction_count,
        },
    }
