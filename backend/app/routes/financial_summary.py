# ============================================================
# FINANCIAL OS
# FINANCIAL DATA ENGINE - SUMMARY
# ============================================================
#
# Version: 1.2
#
# Purpose:
#   Create one read-only financial snapshot and support
#   time-based cash-flow analysis.
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
#
# ============================================================


from datetime import date
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id
from app.models import Category, Account, Transaction, LoanMovement

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
# DECIMAL HELPER
# ============================================================

def to_decimal(value):
    """Safely convert database values to Decimal."""

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


def normalized_income_query(db, user_id, start_date=None, end_date=None):
    """Income excluding borrowed principal and principal recovered on loans given."""
    query = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                    - func.coalesce(
                        db.query(LoanMovement.principal_amount)
                        .filter(
                            LoanMovement.transaction_id == Transaction.id,
                            LoanMovement.user_id == user_id,
                            LoanMovement.movement_type == "recovery",
                        )
                        .correlate(Transaction)
                        .scalar_subquery(),
                        0,
                    )
                ),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
            ~Transaction.category.has(Category.name.ilike("loan disbursement")),
        )
    )
    if start_date is not None:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date is not None:
        query = query.filter(Transaction.transaction_date <= end_date)
    return query


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_financial_summary(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Return a read-only financial snapshot.

    Current financial snapshot:

        /api/financial-summary/?user_id=1

    Period analysis:

        /api/financial-summary/
        ?user_id=1
        &start_date=2026-10-01
        &end_date=2026-10-31

    IMPORTANT:

    The investment section remains a CURRENT snapshot because
    the current market-data system provides current prices.

    The period section applies to transaction-based
    income/expense analysis.
    """

    # ========================================================
    # VALIDATE DATE RANGE
    # ========================================================

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date.",
        )

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
    # ALL-TIME INCOME
    # ========================================================

    total_income = normalized_income_query(db, user_id).scalar()

    # ========================================================
    # ALL-TIME EXPENSE
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
    # ALL-TIME NET CASH FLOW
    # ========================================================

    net_cash_flow = (
        total_income
        - total_expense
    )

    # ========================================================
    # ALL-TIME SAVINGS RATE
    # ========================================================

    savings_rate = calculate_percentage(
        net_cash_flow,
        total_income,
    )

    # ========================================================
    # PERIOD CASH FLOW
    # ========================================================
    #
    # This section only filters transaction-based
    # income and expense.
    #
    # We intentionally preserve the existing meaning of
    # total_income and total_expense.
    #
    # Other transaction types such as:
    # refund
    # interest
    # dividend
    # withdrawal
    # tax
    # loan_repayment
    #
    # are NOT silently reclassified here.
    #
    # ========================================================

    period_income_query = normalized_income_query(db, user_id, start_date, end_date)

    period_expense_query = (
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
    )

    period_count_query = (
        db.query(
            func.count(Transaction.id)
        )
        .filter(
            Transaction.user_id == user_id,
        )
    )

    # --------------------------------------------------------
    # APPLY START DATE
    # --------------------------------------------------------

    if start_date is not None:

        period_income_query = (
            period_income_query.filter(
                Transaction.transaction_date
                >= start_date
            )
        )

        period_expense_query = (
            period_expense_query.filter(
                Transaction.transaction_date
                >= start_date
            )
        )

        period_count_query = (
            period_count_query.filter(
                Transaction.transaction_date
                >= start_date
            )
        )

    # --------------------------------------------------------
    # APPLY END DATE
    # --------------------------------------------------------

    if end_date is not None:

        period_income_query = (
            period_income_query.filter(
                Transaction.transaction_date
                <= end_date
            )
        )

        period_expense_query = (
            period_expense_query.filter(
                Transaction.transaction_date
                <= end_date
            )
        )

        period_count_query = (
            period_count_query.filter(
                Transaction.transaction_date
                <= end_date
            )
        )

    # --------------------------------------------------------
    # EXECUTE PERIOD QUERIES
    # --------------------------------------------------------

    period_income = to_decimal(
        period_income_query.scalar()
    )

    period_expense = to_decimal(
        period_expense_query.scalar()
    )

    period_transaction_count = (
        period_count_query.scalar()
        or 0
    )

    period_net_cash_flow = (
        period_income
        - period_expense
    )

    period_savings_rate = calculate_percentage(
        period_net_cash_flow,
        period_income,
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

    investment_return = calculate_percentage(
        total_gain_loss,
        investment_cost_basis,
    )

    # ========================================================
    # NET WORTH
    # ========================================================

    net_worth = (
        total_balance
        + investment_current_value
    )

    # ========================================================
    # PERIOD DESCRIPTION
    # ========================================================

    if (
        start_date is None
        and end_date is None
    ):

        period_scope = "all_time"

    else:

        period_scope = "custom"

    # ========================================================
    # RETURN FINANCIAL SNAPSHOT
    # ========================================================

    return {
        "status": "success",

        "user_id": user_id,

        "engine": {
            "name": "Financial Data Engine",
            "version": "1.2",
            "read_only": True,
        },

        # ----------------------------------------------------
        # CURRENT CASH
        # ----------------------------------------------------

        "cash": {
            "account_count": account_count,
            "total_balance": total_balance,
        },

        # ----------------------------------------------------
        # ALL-TIME CASH FLOW
        # ----------------------------------------------------

        "cash_flow": {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_cash_flow": net_cash_flow,
            "savings_rate_percent": savings_rate,
        },

        # ----------------------------------------------------
        # PERIOD CASH FLOW
        # ----------------------------------------------------

        "period": {
            "scope": period_scope,
            "start_date": start_date,
            "end_date": end_date,
            "transaction_count": period_transaction_count,
            "income": period_income,
            "expense": period_expense,
            "net_cash_flow": period_net_cash_flow,
            "savings_rate_percent": period_savings_rate,
        },

        # ----------------------------------------------------
        # CURRENT INVESTMENT SNAPSHOT
        # ----------------------------------------------------

        "investments": {
            "holding_count": len(holdings),
            "total_cost_basis": investment_cost_basis,
            "current_value": investment_current_value,
            "realised_gain_loss": realised_gain_loss,
            "unrealised_gain_loss": unrealised_gain_loss,
            "total_gain_loss": total_gain_loss,
            "return_percent": investment_return,
        },

        # ----------------------------------------------------
        # CURRENT NET WORTH
        # ----------------------------------------------------

        "net_worth": {
            "total": net_worth,
        },
    }


# ============================================================
# LOAN MOVEMENTS FOR WEALTH MANAGER CHART NORMALIZATION
# ============================================================

@router.get("/loan-movements", dependencies=[Depends(require_matching_user_id)])
def get_loan_movements_for_summary(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Return movement splits for cash-flow chart normalization only."""
    rows = (
        db.query(LoanMovement, Transaction)
        .join(Transaction, Transaction.id == LoanMovement.transaction_id)
        .filter(LoanMovement.user_id == user_id, Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc(), LoanMovement.id.desc())
        .all()
    )
    return [
        {
            # Movement ID is required for the managed correction/cancellation UI.
            "id": movement.id,
            "transaction_id": movement.transaction_id,
            "loan_id": movement.loan_id,
            "receivable_id": movement.receivable_id,
            "movement_type": movement.movement_type,
            "principal_amount": float(movement.principal_amount or 0),
            "interest_amount": float(movement.interest_amount or 0),
            "fee_amount": float(movement.fee_amount or 0),
            "account_id": transaction.account_id,
            "transaction_type": transaction.transaction_type,
            "amount": float(transaction.amount or 0),
            "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            "description": transaction.description or "",
            "reference": transaction.reference,
        }
        for movement, transaction in rows
    ]
