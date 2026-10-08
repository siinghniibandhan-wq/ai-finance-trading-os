# ============================================================
# FINANCIAL OS
# INVESTMENT TRANSACTION API
# ============================================================
#
# Purpose:
# - Store BUY / SELL investment transactions
# - Keep a permanent transaction ledger
# - This will later power Holdings, Cost Basis and P&L
#
# IMPORTANT:
# - Does NOT replace the existing investments table
# - Does NOT change current Portfolio calculations
# - Does NOT affect Market API
# ============================================================

from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/investment-transactions",
    tags=["Investment Transactions"],
)


# ============================================================
# DATABASE TABLE
# ============================================================

def ensure_transaction_table(db: Session):

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS investment_transactions (

                id SERIAL PRIMARY KEY,

                user_id INTEGER NOT NULL,

                investment_id INTEGER NOT NULL,

                transaction_type VARCHAR(10) NOT NULL,

                quantity NUMERIC(18,6) NOT NULL,

                price NUMERIC(18,4) NOT NULL,

                fees NUMERIC(18,2) DEFAULT 0,

                transaction_date DATE NOT NULL,

                notes TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT investment_transaction_type_check
                    CHECK (
                        transaction_type IN ('BUY', 'SELL')
                    ),

                CONSTRAINT investment_transaction_quantity_check
                    CHECK (quantity > 0),

                CONSTRAINT investment_transaction_price_check
                    CHECK (price > 0),

                CONSTRAINT investment_transaction_fees_check
                    CHECK (fees >= 0)
            )
            """
        )
    )

    db.commit()


# ============================================================
# PYDANTIC SCHEMA
# ============================================================

class InvestmentTransactionCreate(BaseModel):

    user_id: int

    investment_id: int

    transaction_type: str = Field(
        min_length=3,
        max_length=4
    )

    quantity: Decimal = Field(
        gt=0
    )

    price: Decimal = Field(
        gt=0
    )

    fees: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    transaction_date: date

    notes: str | None = None


# ============================================================
# LIST TRANSACTIONS
# ============================================================

@router.get("/")
def list_transactions(
    user_id: int,
    investment_id: int | None = None,
    db: Session = Depends(get_db),
):

    ensure_transaction_table(db)

    if investment_id is not None:

        result = db.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    investment_id,
                    transaction_type,
                    quantity,
                    price,
                    fees,
                    transaction_date,
                    notes,
                    created_at,
                    updated_at
                FROM investment_transactions
                WHERE user_id = :user_id
                  AND investment_id = :investment_id
                ORDER BY transaction_date ASC, id ASC
                """
            ),
            {
                "user_id": user_id,
                "investment_id": investment_id,
            },
        )

    else:

        result = db.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    investment_id,
                    transaction_type,
                    quantity,
                    price,
                    fees,
                    transaction_date,
                    notes,
                    created_at,
                    updated_at
                FROM investment_transactions
                WHERE user_id = :user_id
                ORDER BY transaction_date ASC, id ASC
                """
            ),
            {
                "user_id": user_id,
            },
        )

    return [
        dict(row._mapping)
        for row in result
    ]


# ============================================================
# CREATE BUY / SELL TRANSACTION
# ============================================================

@router.post("/", status_code=201)
def create_transaction(
    data: InvestmentTransactionCreate,
    db: Session = Depends(get_db),
):
    ensure_transaction_table(db)

    # --------------------------------------------------------
    # NORMALIZE TRANSACTION TYPE
    # --------------------------------------------------------

    transaction_type = data.transaction_type.strip().upper()

    if transaction_type not in {"BUY", "SELL"}:
        raise HTTPException(
            status_code=400,
            detail="Transaction type must be BUY or SELL.",
        )

    # --------------------------------------------------------
    # FIND INVESTMENT
    # --------------------------------------------------------

    investment_result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                quantity
            FROM investments
            WHERE id = :investment_id
              AND user_id = :user_id
            """
        ),
        {
            "investment_id": data.investment_id,
            "user_id": data.user_id,
        },
    )

    investment = investment_result.first()

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found for this user.",
        )

    # --------------------------------------------------------
    # CHECK CURRENT LEDGER HOLDING
    # --------------------------------------------------------

    balance_result = db.execute(
        text(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'BUY'
                            THEN quantity
                            WHEN transaction_type = 'SELL'
                            THEN -quantity
                            ELSE 0
                        END
                    ),
                    0
                ) AS available_quantity
            FROM investment_transactions
            WHERE user_id = :user_id
              AND investment_id = :investment_id
            """
        ),
        {
            "user_id": data.user_id,
            "investment_id": data.investment_id,
        },
    )

    balance_row = balance_result.first()

    available_quantity = Decimal(
        str(
            balance_row.available_quantity
            if balance_row
            else 0
        )
    )

    # --------------------------------------------------------
    # SELL VALIDATION
    # --------------------------------------------------------

    if transaction_type == "SELL":

        if data.quantity > available_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Insufficient holding quantity. "
                    f"Available: {available_quantity}"
                ),
            )

    # --------------------------------------------------------
    # CALCULATE NEW HOLDING
    # --------------------------------------------------------

    if transaction_type == "BUY":

        new_quantity = (
            available_quantity
            + data.quantity
        )

    else:

        new_quantity = (
            available_quantity
            - data.quantity
        )

    # --------------------------------------------------------
    # INSERT TRANSACTION
    # --------------------------------------------------------

    result = db.execute(
        text(
            """
            INSERT INTO investment_transactions (
                user_id,
                investment_id,
                transaction_type,
                quantity,
                price,
                fees,
                transaction_date,
                notes
            )
            VALUES (
                :user_id,
                :investment_id,
                :transaction_type,
                :quantity,
                :price,
                :fees,
                :transaction_date,
                :notes
            )
            RETURNING
                id,
                user_id,
                investment_id,
                transaction_type,
                quantity,
                price,
                fees,
                transaction_date,
                notes,
                created_at,
                updated_at
            """
        ),
        {
            "user_id": data.user_id,
            "investment_id": data.investment_id,
            "transaction_type": transaction_type,
            "quantity": data.quantity,
            "price": data.price,
            "fees": data.fees,
            "transaction_date": data.transaction_date,
            "notes": data.notes,
        },
    )

    transaction = result.first()

    if not transaction:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to create investment transaction.",
        )

    # --------------------------------------------------------
    # SYNC INVESTMENT QUANTITY
    # --------------------------------------------------------

    db.execute(
        text(
            """
            UPDATE investments
            SET
                quantity = :quantity,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :investment_id
              AND user_id = :user_id
            """
        ),
        {
            "quantity": new_quantity,
            "investment_id": data.investment_id,
            "user_id": data.user_id,
        },
    )

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    db.commit()

    return dict(transaction._mapping)



# ============================================================
# GET SINGLE TRANSACTION
# ============================================================

@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    ensure_transaction_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                investment_id,
                transaction_type,
                quantity,
                price,
                fees,
                transaction_date,
                notes,
                created_at,
                updated_at
            FROM investment_transactions
            WHERE id = :transaction_id
            """
        ),
        {
            "transaction_id": transaction_id,
        },
    )

    transaction = result.first()

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail="Investment transaction not found.",
        )

    return dict(transaction._mapping)


# ============================================================
# DELETE TRANSACTION
# ============================================================

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    ensure_transaction_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM investment_transactions
            WHERE id = :transaction_id
            RETURNING id
            """
        ),
        {
            "transaction_id": transaction_id,
        },
    )

    deleted = result.first()

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Investment transaction not found.",
        )

    db.commit()

    return {
        "status": "deleted",
        "transaction_id": transaction_id,
  }
