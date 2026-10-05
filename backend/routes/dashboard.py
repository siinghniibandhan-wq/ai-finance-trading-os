from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Asset, Liability, Transaction
from database.schemas import (
    DashboardSummary,
    NetWorthResponse,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
)
def dashboard_summary(
    db: Session = Depends(get_db),
):
    total_assets = (
        db.query(
            func.coalesce(
                func.sum(Asset.current_value),
                0,
            )
        )
        .filter(Asset.is_active.is_(True))
        .scalar()
    )

    total_liabilities = (
        db.query(
            func.coalesce(
                func.sum(Liability.outstanding_amount),
                0,
            )
        )
        .filter(Liability.is_active.is_(True))
        .scalar()
    )

    total_income = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.is_deleted.is_(False),
            Transaction.transaction_type.in_(
                [
                    "income",
                    "refund",
                    "interest",
                    "dividend",
                ]
            ),
        )
        .scalar()
    )

    total_expenses = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.is_deleted.is_(False),
            Transaction.transaction_type.in_(
                [
                    "expense",
                    "tax",
                    "loan_repayment",
                ]
            ),
        )
        .scalar()
    )

    total_investments = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.is_deleted.is_(False),
            Transaction.transaction_type == "investment",
        )
        .scalar()
    )

    net_worth = (
        Decimal(str(total_assets))
        - Decimal(str(total_liabilities))
    )

    return DashboardSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
        total_income=total_income,
        total_expenses=total_expenses,
        total_investments=total_investments,
    )


@router.get(
    "/net-worth",
    response_model=NetWorthResponse,
)
def net_worth(
    db: Session = Depends(get_db),
):
    total_assets = (
        db.query(
            func.coalesce(
                func.sum(Asset.current_value),
                0,
            )
        )
        .filter(Asset.is_active.is_(True))
        .scalar()
    )

    total_liabilities = (
        db.query(
            func.coalesce(
                func.sum(Liability.outstanding_amount),
                0,
            )
        )
        .filter(Liability.is_active.is_(True))
        .scalar()
    )

    net_worth_value = (
        Decimal(str(total_assets))
        - Decimal(str(total_liabilities))
    )

    return NetWorthResponse(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth_value,
  )
