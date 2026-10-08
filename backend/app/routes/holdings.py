# ============================================================
# FINANCIAL OS
# HOLDINGS ENGINE
# ============================================================
#
# Purpose:
# - Calculate actual holdings from BUY / SELL transactions
# - Calculate current portfolio value
# - Calculate unrealised gain/loss
# - Use the existing investments table
# - Use the investment_transactions ledger
#
# Formula:
#
# BUY quantity
# + BUY quantity
# - SELL quantity
# = CURRENT HOLDING
#
# IMPORTANT:
# - Does NOT modify existing investment records
# - Does NOT modify investment transactions
# - Does NOT replace Portfolio API
# ============================================================

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db

router = APIRouter(
    prefix="/api/holdings",
    tags=["Holdings"],
)


# ============================================================
# GET ALL HOLDINGS
# ============================================================

@router.get("/")
def get_holdings(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate actual holdings from investment transactions.
    """

    result = db.execute(
        text(
            """
            SELECT
                i.id AS investment_id,
                i.name,
                i.symbol,
                i.investment_type,

                COALESCE(
                    SUM(
                        CASE
                            WHEN it.transaction_type = 'BUY'
                            THEN it.quantity
                            WHEN it.transaction_type = 'SELL'
                            THEN -it.quantity
                            ELSE 0
                        END
                    ),
                    0
                ) AS quantity_held,

                COALESCE(i.current_price, 0) AS current_price

            FROM investments i

            LEFT JOIN investment_transactions it
                ON it.investment_id = i.id
                AND it.user_id = i.user_id

            WHERE i.user_id = :user_id

            GROUP BY
                i.id,
                i.name,
                i.symbol,
                i.investment_type,
                i.current_price

            ORDER BY i.id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    holdings = []

    for row in result:
        quantity = Decimal(str(row.quantity_held or 0))
        current_price = Decimal(str(row.current_price or 0))

        current_value = quantity * current_price

        holdings.append(
            {
                "investment_id": row.investment_id,
                "name": row.name,
                "symbol": row.symbol,
                "investment_type": row.investment_type,
                "quantity_held": quantity,
                "current_price": current_price,
                "current_value": current_value,
            }
        )

    return {
        "status": "success",
        "user_id": user_id,
        "count": len(holdings),
        "holdings": holdings,
    }


# ============================================================
# GET HOLDING FOR ONE INVESTMENT
# ============================================================

@router.get("/{investment_id}")
def get_holding(
    investment_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate the current holding for one investment.
    """

    result = db.execute(
        text(
            """
            SELECT
                i.id AS investment_id,
                i.name,
                i.symbol,
                i.investment_type,

                COALESCE(
                    SUM(
                        CASE
                            WHEN it.transaction_type = 'BUY'
                            THEN it.quantity
                            WHEN it.transaction_type = 'SELL'
                            THEN -it.quantity
                            ELSE 0
                        END
                    ),
                    0
                ) AS quantity_held,

                COALESCE(i.current_price, 0) AS current_price

            FROM investments i

            LEFT JOIN investment_transactions it
                ON it.investment_id = i.id
                AND it.user_id = i.user_id

            WHERE i.id = :investment_id
              AND i.user_id = :user_id

            GROUP BY
                i.id,
                i.name,
                i.symbol,
                i.investment_type,
                i.current_price
            """
        ),
        {
            "investment_id": investment_id,
            "user_id": user_id,
        },
    )

    row = result.first()

    if not row:
        return {
            "status": "error",
            "message": "Investment not found.",
        }

    quantity = Decimal(str(row.quantity_held or 0))
    current_price = Decimal(str(row.current_price or 0))

    current_value = quantity * current_price

    return {
        "status": "success",
        "investment_id": row.investment_id,
        "name": row.name,
        "symbol": row.symbol,
        "investment_type": row.investment_type,
        "quantity_held": quantity,
        "current_price": current_price,
        "current_value": current_value,
    }
