# ============================================================
# FINANCIAL OS
# TAX DATA ENGINE
# ============================================================
#
# Version: 1.0
#
# Purpose:
#   Provide a read-only India-focused tax data snapshot
#   from existing Financial OS transaction and investment data.
#
# Current data:
#   1. Financial year
#   2. Income transactions
#   3. Interest transactions
#   4. Dividend transactions
#   5. Tax transactions
#   6. Refund transactions
#   7. Investment P&L snapshot
#   8. Transaction count
#
# IMPORTANT:
#   This module does NOT calculate final tax liability.
#
#   It does NOT modify:
#   - Transactions
#   - Accounts
#   - Investments
#   - Holdings
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

from sqlalchemy import (
    func,
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id

from app.models import Transaction

from app.routes.holdings import (
    load_investments,
    load_transactions,
    build_holdings,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tax-data",
    tags=["Tax Data"],
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
# FINANCIAL YEAR HELPER
# ============================================================

def get_financial_year_dates(
    financial_year: str,
):
    """
    Convert Indian financial year format:

        2026-27

    into:

        2026-04-01
        2027-03-31
    """

    try:

        parts = financial_year.split("-")

        if len(parts) != 2:
            raise ValueError

        start_year = int(parts[0])
        end_year_short = int(parts[1])

        if (
            start_year < 2000
            or start_year > 2100
        ):
            raise ValueError

        if end_year_short != (
            start_year + 1
        ) % 100:
            raise ValueError

        start_date = date(
            start_year,
            4,
            1,
        )

        end_date = date(
            start_year + 1,
            3,
            31,
        )

        return (
            start_date,
            end_date,
        )

    except (
        ValueError,
        TypeError,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "financial_year must use "
                "the format YYYY-YY, "
                "for example 2026-27."
            ),
        )


# ============================================================
# TAX DATA
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_tax_data(
    user_id: int,
    financial_year: str = "2026-27",
    db: Session = Depends(get_db),
):
    """
    Return a read-only tax data snapshot.

    Example:

        GET /api/tax-data/?user_id=1

    Or:

        GET /api/tax-data/
        ?user_id=1
        &financial_year=2026-27

    IMPORTANT:

        This endpoint reports financial data only.

        It does NOT determine:
        - taxable income
        - tax slab
        - deductions
        - final tax liability
        - ITR filing result
    """


    # ========================================================
    # FINANCIAL YEAR
    # ========================================================

    start_date, end_date = (
        get_financial_year_dates(
            financial_year
        )
    )


    # ========================================================
    # BASE QUERY
    # ========================================================

    base_query = (
        db.query(
            func.count(
                Transaction.id
            ).label(
                "transaction_count"
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    transaction_count = (
        base_query
        .scalar()
        or 0
    )


    # ========================================================
    # INCOME
    # ========================================================

    income = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    income = to_decimal(
        income
    )


    # ========================================================
    # INTEREST
    # ========================================================

    interest = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "interest",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    interest = to_decimal(
        interest
    )


    # ========================================================
    # DIVIDEND
    # ========================================================

    dividend = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "dividend",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    dividend = to_decimal(
        dividend
    )


    # ========================================================
    # TAX PAYMENTS
    # ========================================================

    tax_paid = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "tax",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    tax_paid = to_decimal(
        tax_paid
    )


    # ========================================================
    # REFUNDS
    # ========================================================

    refunds = (
        db.query(
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "refund",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    refunds = to_decimal(
        refunds
    )


    # ========================================================
    # REPORTED RECEIPTS
    # ========================================================
    #
    # This is a data aggregation only.
    #
    # It is NOT "taxable income".
    #
    # ========================================================

    reported_receipts = (
        income
        + interest
        + dividend
    )


    # ========================================================
    # INVESTMENT SNAPSHOT
    # ========================================================
    #
    # Current holdings/P&L are loaded from the existing
    # holdings engine.
    #
    # This is a CURRENT snapshot, not a financial-year
    # capital-gains calculation.
    #
    # ========================================================

    investments = load_investments(
        db,
        user_id,
    )

    investment_transactions = (
        load_transactions(
            db,
            user_id,
        )
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
    # RETURN TAX DATA
    # ========================================================

    return {
        "status": "success",

        "user_id": user_id,

        "tax_engine": {
            "name": "Tax Data Engine",
            "version": "1.0",
            "read_only": True,
            "country": "India",
        },

        "financial_year": {
            "financial_year": financial_year,
            "start_date": start_date,
            "end_date": end_date,
        },

        "income_data": {
            "income": income,
            "interest": interest,
            "dividend": dividend,
            "reported_receipts": reported_receipts,
        },

        "tax_data": {
            "tax_paid": tax_paid,
            "refunds": refunds,
        },

        "investment_data": {
            "holding_count": len(
                holdings
            ),
            "cost_basis": (
                investment_cost_basis
            ),
            "current_value": (
                investment_current_value
            ),
            "realised_gain_loss": (
                realised_gain_loss
            ),
            "unrealised_gain_loss": (
                unrealised_gain_loss
            ),
            "total_gain_loss": (
                total_gain_loss
            ),
        },

        "activity": {
            "transaction_count": (
                transaction_count
            ),
        },

        "tax_calculation": {
            "status": "not_calculated",
            "message": (
                "Tax liability is not calculated "
                "by Tax Data Engine v1.0."
            ),
        },
    }
