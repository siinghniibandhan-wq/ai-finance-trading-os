# ============================================================
# FINANCIAL OS
# FINANCIAL ANALYTICS ENGINE
# ============================================================
#
# Version: 1.0
#
# Purpose:
#   Provide read-only financial analytics from the existing
#   transaction and category data.
#
# Current analytics:
#   1. Expense by category
#   2. Monthly cash flow
#   3. Period summary
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


from datetime import date
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import (
    and_,
    case,
    extract,
    func,
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import (
    Category,
    LoanMovement,
    Transaction,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/financial-analytics",
    tags=["Financial Analytics"],
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


def _ordinary_income_expression():
    """
    Calculate ordinary income without counting borrowed principal
    or the principal portion of loan recoveries as income.

    Loan recovery transactions store principal + interest + fees as
    one cash inflow; LoanMovement identifies the principal portion.
    """
    is_ordinary_income = and_(
        Transaction.transaction_type == "income",
        ~Transaction.category.has(Category.name.ilike("loan disbursement")),
    )
    return case(
        (
            is_ordinary_income,
            Transaction.amount - func.coalesce(LoanMovement.principal_amount, 0),
        ),
        else_=0,
    )


# ============================================================
# PERIOD VALIDATION
# ============================================================

def validate_dates(
    start_date,
    end_date,
):
    """
    Validate an optional date range.
    """

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date.",
        )


# ============================================================
# EXPENSE BY CATEGORY
# ============================================================

@router.get("/expenses-by-category")
def expenses_by_category(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Return expenses grouped by category.

    Example:

    /api/financial-analytics/expenses-by-category/
    ?user_id=1
    """

    validate_dates(
        start_date,
        end_date,
    )

    query = (
        db.query(
            Category.id.label(
                "category_id"
            ),
            Category.name.label(
                "category_name"
            ),
            func.coalesce(
                func.sum(
                    Transaction.amount
                ),
                0,
            ).label(
                "total_expense"
            ),
        )
        .join(
            Transaction,
            Transaction.category_id
            == Category.id,
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type
            == "expense",
        )
    )

    # --------------------------------------------------------
    # START DATE
    # --------------------------------------------------------

    if start_date is not None:

        query = query.filter(
            Transaction.transaction_date
            >= start_date
        )

    # --------------------------------------------------------
    # END DATE
    # --------------------------------------------------------

    if end_date is not None:

        query = query.filter(
            Transaction.transaction_date
            <= end_date
        )

    # --------------------------------------------------------
    # GROUP
    # --------------------------------------------------------

    rows = (
        query
        .group_by(
            Category.id,
            Category.name,
        )
        .order_by(
            func.sum(
                Transaction.amount
            ).desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    categories = []

    total_expense = Decimal("0")

    for row in rows:

        amount = to_decimal(
            row.total_expense
        )

        total_expense += amount

        categories.append(
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "expense": amount,
            }
        )

    return {
        "status": "success",

        "user_id": user_id,

        "analytics": {
            "name": "Financial Analytics Engine",
            "version": "1.0",
            "read_only": True,
        },

        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },

        "total_expense": total_expense,

        "categories": categories,
    }


# ============================================================
# MONTHLY CASH FLOW
# ============================================================

@router.get("/monthly-cash-flow")
def monthly_cash_flow(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Return monthly income, expense and net cash flow.

    Example:

    /api/financial-analytics/monthly-cash-flow/
    ?user_id=1
    """

    validate_dates(
        start_date,
        end_date,
    )

    query = (
        db.query(
            extract(
                "year",
                Transaction.transaction_date,
            ).label("year"),

            extract(
                "month",
                Transaction.transaction_date,
            ).label("month"),

            func.coalesce(
                func.sum(
_ordinary_income_expression()
                ),
                0,
            ).label(
                "income"
            ),

            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type
                            == "expense",
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label(
                "expense"
            ),
        )
        .outerjoin(LoanMovement, LoanMovement.transaction_id == Transaction.id)
        .filter(
            Transaction.user_id == user_id,
        )
    )

    # --------------------------------------------------------
    # START DATE
    # --------------------------------------------------------

    if start_date is not None:

        query = query.filter(
            Transaction.transaction_date
            >= start_date
        )

    # --------------------------------------------------------
    # END DATE
    # --------------------------------------------------------

    if end_date is not None:

        query = query.filter(
            Transaction.transaction_date
            <= end_date
        )

    # --------------------------------------------------------
    # GROUP BY MONTH
    # --------------------------------------------------------

    rows = (
        query
        .group_by(
            extract(
                "year",
                Transaction.transaction_date,
            ),
            extract(
                "month",
                Transaction.transaction_date,
            ),
        )
        .order_by(
            extract(
                "year",
                Transaction.transaction_date,
            ),
            extract(
                "month",
                Transaction.transaction_date,
            ),
        )
        .all()
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    months = []

    for row in rows:

        income = to_decimal(
            row.income
        )

        expense = to_decimal(
            row.expense
        )

        net_cash_flow = (
            income
            - expense
        )

        months.append(
            {
                "year": int(row.year),
                "month": int(row.month),
                "income": income,
                "expense": expense,
                "net_cash_flow": net_cash_flow,
            }
        )

    return {
        "status": "success",

        "user_id": user_id,

        "analytics": {
            "name": "Financial Analytics Engine",
            "version": "1.0",
            "read_only": True,
        },

        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },

        "months": months,
    }


# ============================================================
# PERIOD SUMMARY
# ============================================================

@router.get("/period-summary")
def period_summary(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Return a compact transaction-based period summary.
    """

    validate_dates(
        start_date,
        end_date,
    )

    query = (
        db.query(
            func.count(
                Transaction.id
            ).label(
                "transaction_count"
            ),

            func.coalesce(
                func.sum(
_ordinary_income_expression()
                ),
                0,
            ).label(
                "income"
            ),

            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type
                            == "expense",
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label(
                "expense"
            ),
        )
        .outerjoin(LoanMovement, LoanMovement.transaction_id == Transaction.id)
        .filter(
            Transaction.user_id == user_id,
        )
    )

    # --------------------------------------------------------
    # START DATE
    # --------------------------------------------------------

    if start_date is not None:

        query = query.filter(
            Transaction.transaction_date
            >= start_date
        )

    # --------------------------------------------------------
    # END DATE
    # --------------------------------------------------------

    if end_date is not None:

        query = query.filter(
            Transaction.transaction_date
            <= end_date
        )

    row = query.one()

    income = to_decimal(
        row.income
    )

    expense = to_decimal(
        row.expense
    )

    net_cash_flow = (
        income
        - expense
    )

    return {
        "status": "success",

        "user_id": user_id,

        "analytics": {
            "name": "Financial Analytics Engine",
            "version": "1.0",
            "read_only": True,
        },

        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },

        "summary": {
            "transaction_count": (
                row.transaction_count
            ),
            "income": income,
            "expense": expense,
            "net_cash_flow": net_cash_flow,
        },
    }
