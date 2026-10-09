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

                status VARCHAR(12) NOT NULL DEFAULT 'ACTIVE',
                void_reason TEXT,
                voided_at TIMESTAMP,

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

    # Safe additive migration for existing databases.
    db.execute(text("ALTER TABLE investment_transactions ADD COLUMN IF NOT EXISTS status VARCHAR(12) NOT NULL DEFAULT 'ACTIVE'"))
    db.execute(text("ALTER TABLE investment_transactions ADD COLUMN IF NOT EXISTS void_reason TEXT"))
    db.execute(text("ALTER TABLE investment_transactions ADD COLUMN IF NOT EXISTS voided_at TIMESTAMP"))
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


class InvestmentTransactionUpdate(BaseModel):
    transaction_type: str = Field(min_length=3, max_length=4)
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    fees: Decimal = Field(default=Decimal("0"), ge=0)
    transaction_date: date
    notes: str | None = None


class InvestmentTransactionVoid(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


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
                    status,
                    void_reason,
                    voided_at,
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
                    status,
                    void_reason,
                    voided_at,
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
              AND status = 'ACTIVE'
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
                status,
                void_reason,
                voided_at,
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
# EDIT TRANSACTION (ACTIVE RECORDS ONLY)
# ============================================================

@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: InvestmentTransactionUpdate,
    user_id: int,
    db: Session = Depends(get_db),
):
    ensure_transaction_table(db)
    transaction_type = data.transaction_type.strip().upper()
    if transaction_type not in {"BUY", "SELL"}:
        raise HTTPException(status_code=400, detail="Transaction type must be BUY or SELL.")

    existing = db.execute(text("""
        SELECT * FROM investment_transactions
        WHERE id = :id AND user_id = :user_id
        FOR UPDATE
    """), {"id": transaction_id, "user_id": user_id}).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Investment transaction not found.")
    if existing.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Only active transactions can be edited.")

    # Validate that all active transactions remain non-negative when ordered by date.
    rows = db.execute(text("""
        SELECT id, transaction_type, quantity, transaction_date
        FROM investment_transactions
        WHERE user_id = :user_id AND investment_id = :investment_id
          AND status = 'ACTIVE' AND id <> :id
        ORDER BY transaction_date, id
    """), {"user_id": user_id, "investment_id": existing.investment_id, "id": transaction_id}).fetchall()
    running = Decimal("0")
    timeline = [{"id": int(r.id), "type": r.transaction_type, "qty": Decimal(str(r.quantity)), "date": r.transaction_date} for r in rows]
    timeline.append({"id": transaction_id, "type": transaction_type, "qty": data.quantity, "date": data.transaction_date})
    timeline.sort(key=lambda r: (r["date"], r["id"]))
    for item in timeline:
        running += item["qty"] if item["type"] == "BUY" else -item["qty"]
        if running < 0:
            raise HTTPException(status_code=400, detail="This edit would create a negative holding. Review subsequent SELL transactions first.")

    updated = db.execute(text("""
        UPDATE investment_transactions SET
            transaction_type = :transaction_type,
            quantity = :quantity,
            price = :price,
            fees = :fees,
            transaction_date = :transaction_date,
            notes = :notes,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :id AND user_id = :user_id
        RETURNING id, user_id, investment_id, transaction_type, quantity,
                  price, fees, transaction_date, notes, status, void_reason,
                  voided_at, created_at, updated_at
    """), {
        "id": transaction_id, "user_id": user_id,
        "transaction_type": transaction_type, "quantity": data.quantity,
        "price": data.price, "fees": data.fees,
        "transaction_date": data.transaction_date, "notes": data.notes,
    }).first()

    active_balance = db.execute(text("""
        SELECT COALESCE(SUM(CASE WHEN transaction_type = 'BUY' THEN quantity ELSE -quantity END), 0) AS quantity
        FROM investment_transactions
        WHERE user_id = :user_id AND investment_id = :investment_id AND status = 'ACTIVE'
    """), {"user_id": user_id, "investment_id": existing.investment_id}).first()
    db.execute(text("""
        UPDATE investments SET quantity = :quantity, updated_at = CURRENT_TIMESTAMP
        WHERE id = :investment_id AND user_id = :user_id
    """), {"quantity": Decimal(str(active_balance.quantity or 0)), "investment_id": existing.investment_id, "user_id": user_id})
    db.commit()
    return dict(updated._mapping)


# ============================================================
# VOID TRANSACTION (AUDIT-PRESERVING; NOT HARD DELETE)
# ============================================================

@router.post("/{transaction_id}/void")
def void_transaction(
    transaction_id: int,
    data: InvestmentTransactionVoid,
    user_id: int,
    db: Session = Depends(get_db),
):
    ensure_transaction_table(db)
    existing = db.execute(text("""
        SELECT * FROM investment_transactions
        WHERE id = :id AND user_id = :user_id
        FOR UPDATE
    """), {"id": transaction_id, "user_id": user_id}).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Investment transaction not found.")
    if existing.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Transaction is already voided or inactive.")

    # Ensure voiding this BUY will not leave any later active SELL unsupported.
    rows = db.execute(text("""
        SELECT id, transaction_type, quantity, transaction_date
        FROM investment_transactions
        WHERE user_id = :user_id AND investment_id = :investment_id
          AND status = 'ACTIVE' AND id <> :id
        ORDER BY transaction_date, id
    """), {"user_id": user_id, "investment_id": existing.investment_id, "id": transaction_id}).fetchall()
    timeline = [{"id": int(r.id), "type": r.transaction_type, "qty": Decimal(str(r.quantity)), "date": r.transaction_date} for r in rows]
    timeline.sort(key=lambda r: (r["date"], r["id"]))
    running = Decimal("0")
    for item in timeline:
        running += item["qty"] if item["type"] == "BUY" else -item["qty"]
        if running < 0:
            raise HTTPException(status_code=409, detail="Voiding this transaction would make later SELL activity exceed available BUY quantity. Correct or reverse dependent transactions first.")

    db.execute(text("""
        UPDATE investment_transactions
        SET status = 'VOIDED', void_reason = :reason,
            voided_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = :id AND user_id = :user_id
    """), {"id": transaction_id, "user_id": user_id, "reason": data.reason.strip()})

    # Keep the legacy investment quantity in sync with active ledger balance.
    balance = db.execute(text("""
        SELECT COALESCE(SUM(CASE WHEN transaction_type = 'BUY' THEN quantity ELSE -quantity END), 0) AS quantity
        FROM investment_transactions
        WHERE user_id = :user_id AND investment_id = :investment_id AND status = 'ACTIVE'
    """), {"user_id": user_id, "investment_id": existing.investment_id}).first()
    db.execute(text("""
        UPDATE investments SET quantity = :quantity, updated_at = CURRENT_TIMESTAMP
        WHERE id = :investment_id AND user_id = :user_id
    """), {"quantity": Decimal(str(balance.quantity or 0)), "investment_id": existing.investment_id, "user_id": user_id})
    db.commit()
    return {"status": "voided", "transaction_id": transaction_id, "reason": data.reason.strip(), "active_quantity": str(balance.quantity or 0)}


# ============================================================
# LEGACY DELETE ENDPOINT DISABLED TO PRESERVE AUDIT HISTORY
# ============================================================

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=405,
        detail="Permanent deletion is disabled. Use POST /{transaction_id}/void with user_id and a reason to preserve audit history.",
    )
