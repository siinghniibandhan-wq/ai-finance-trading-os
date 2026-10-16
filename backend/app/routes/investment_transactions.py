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
from app.models import Account, User
from app.finance_diary import record_finance_event
from app.routes.auth import get_current_user


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


def _cash_effect(transaction_type: str, quantity: Decimal, price: Decimal, fees: Decimal) -> Decimal:
    """Signed broker-cash movement: negative for BUY, positive for SELL."""
    gross = quantity * price
    return -(gross + fees) if transaction_type == "BUY" else gross - fees


def _load_locked_broker_account(db: Session, investment_row, user_id: int):
    """Lock the investment's linked broker cash account within this DB transaction."""
    account_id = investment_row["investment_account_id"] if isinstance(investment_row, dict) else investment_row.investment_account_id
    if account_id is None:
        raise HTTPException(status_code=409, detail="This holding has no linked broker cash account. Link/reconcile its broker account before recording or changing trades.")
    account = db.execute(text("""
        SELECT id, name, balance FROM accounts
        WHERE id = :account_id AND user_id = :user_id
          AND account_type = 'investment' AND is_active = TRUE
        FOR UPDATE
    """), {"account_id": account_id, "user_id": user_id}).first()
    if not account:
        raise HTTPException(status_code=409, detail="The linked broker cash account is unavailable. No trade changes were saved.")
    return account


def _apply_cash_delta(db: Session, account, delta: Decimal, user_id: int):
    """Apply a signed cash movement; reject debits that exceed available cash."""
    balance = Decimal(str(account.balance or 0))
    new_balance = balance + delta
    if new_balance < 0:
        db.rollback()
        raise HTTPException(status_code=409, detail="Insufficient cash in the linked broker account for this trade change.")
    db.execute(text("""
        UPDATE accounts SET balance = :balance
        WHERE id = :account_id AND user_id = :user_id
    """), {"balance": new_balance, "account_id": account.id, "user_id": user_id})


def validate_transaction_timeline(rows, candidate_type: str, candidate_quantity: Decimal, candidate_date: date):
    """Validate a proposed transaction against the complete active, date-ordered ledger.

    Returns (quantity_available_before_candidate, final_active_quantity). Raises
    ValueError if the candidate would make holdings negative at any point.
    """
    timeline = []
    max_id = 0
    for row in rows:
        row_id = int(row["id"] if isinstance(row, dict) else row.id)
        row_type = row["transaction_type"] if isinstance(row, dict) else row.transaction_type
        row_quantity = Decimal(str(row["quantity"] if isinstance(row, dict) else row.quantity))
        row_date = row["transaction_date"] if isinstance(row, dict) else row.transaction_date
        timeline.append((row_date, row_id, row_type, row_quantity, False))
        max_id = max(max_id, row_id)

    # A newly created row receives a higher ID than existing rows on the same date.
    timeline.append((candidate_date, max_id + 1, candidate_type, candidate_quantity, True))
    timeline.sort(key=lambda item: (item[0], item[1]))

    running = Decimal("0")
    available_before_candidate = Decimal("0")
    for tx_date, _, tx_type, quantity, is_candidate in timeline:
        if is_candidate:
            available_before_candidate = running
        running += quantity if tx_type == "BUY" else -quantity
        if running < 0:
            if is_candidate:
                raise ValueError(f"Insufficient holding quantity on {tx_date}. Available: {available_before_candidate}")
            raise ValueError(
                f"This transaction would make holdings negative on {tx_date}. "
                "Review later SELL transactions first."
            )
    return available_before_candidate, running


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
    user_id: int | None = None,  # Legacy query parameter is ignored for security.
    investment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

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
    current_user: User = Depends(get_current_user),
):
    # Ignore any user_id in the request body; derive ownership from the token.
    user_id = current_user.id
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
    if transaction_type == "SELL" and data.fees > data.quantity * data.price:
        raise HTTPException(status_code=422, detail="SELL fees cannot exceed gross sale proceeds.")

    # --------------------------------------------------------
    # FIND INVESTMENT
    # --------------------------------------------------------

    investment_result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                quantity,
                investment_account_id
            FROM investments
            WHERE id = :investment_id
              AND user_id = :user_id
            FOR UPDATE
            """
        ),
        {
            "investment_id": data.investment_id,
            "user_id": user_id,
        },
    )

    investment = investment_result.first()

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found for this user.",
        )

    broker_account = _load_locked_broker_account(db, investment, user_id)

    # --------------------------------------------------------
    # VALIDATE THE COMPLETE ACTIVE LEDGER IN DATE ORDER
    # --------------------------------------------------------

    active_rows = db.execute(
        text(
            """
            SELECT id, transaction_type, quantity, transaction_date
            FROM investment_transactions
            WHERE user_id = :user_id
              AND investment_id = :investment_id
              AND status = 'ACTIVE'
            ORDER BY transaction_date ASC, id ASC
            """
        ),
        {
            "user_id": user_id,
            "investment_id": data.investment_id,
        },
    ).fetchall()

    try:
        _, new_quantity = validate_transaction_timeline(
            active_rows,
            transaction_type,
            data.quantity,
            data.transaction_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
            "user_id": user_id,
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
            "user_id": user_id,
        },
    )

    # Cash and ledger commit together: BUY spends cost plus fees; SELL credits net proceeds.
    cash_delta = _cash_effect(transaction_type, data.quantity, data.price, data.fees)
    _apply_cash_delta(db, broker_account, cash_delta, user_id)
    record_finance_event(
        db, user_id=user_id, event_type="created", entity_type="investment_transaction",
        entity_id=transaction.id, description=f"Investment {transaction_type} recorded; broker cash reconciled",
        snapshot={"investment_id": data.investment_id, "account_id": broker_account.id,
                  "transaction_type": transaction_type, "quantity": data.quantity,
                  "price": data.price, "fees": data.fees, "cash_delta": cash_delta},
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
    current_user: User = Depends(get_current_user),
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
            WHERE id = :transaction_id AND user_id = :user_id
            """
        ),
        {
            "transaction_id": transaction_id,
            "user_id": current_user.id,
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
    user_id: int | None = None,  # Legacy query parameter is ignored for security.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    ensure_transaction_table(db)
    transaction_type = data.transaction_type.strip().upper()
    if transaction_type not in {"BUY", "SELL"}:
        raise HTTPException(status_code=400, detail="Transaction type must be BUY or SELL.")
    if transaction_type == "SELL" and data.fees > data.quantity * data.price:
        raise HTTPException(status_code=422, detail="SELL fees cannot exceed gross sale proceeds.")

    # Resolve the parent investment first, then acquire the same parent-row
    # lock used by create_transaction. All ledger mutations for one investment
    # must serialize on this row before reading/validating the active timeline.
    locator = db.execute(text("""
        SELECT investment_id FROM investment_transactions
        WHERE id = :id AND user_id = :user_id
    """), {"id": transaction_id, "user_id": user_id}).first()
    if not locator:
        raise HTTPException(status_code=404, detail="Investment transaction not found.")

    locked_investment = db.execute(text("""
        SELECT id, investment_account_id FROM investments
        WHERE id = :investment_id AND user_id = :user_id
        FOR UPDATE
    """), {"investment_id": locator.investment_id, "user_id": user_id}).first()
    if not locked_investment:
        raise HTTPException(status_code=404, detail="Investment not found for this user.")

    existing = db.execute(text("""
        SELECT * FROM investment_transactions
        WHERE id = :id AND user_id = :user_id
        FOR UPDATE
    """), {"id": transaction_id, "user_id": user_id}).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Investment transaction not found.")
    if existing.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Only active transactions can be edited.")
    broker_account = _load_locked_broker_account(db, locked_investment, user_id)
    old_cash_effect = _cash_effect(
        existing.transaction_type, Decimal(str(existing.quantity)),
        Decimal(str(existing.price)), Decimal(str(existing.fees or 0)),
    )

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
    new_cash_effect = _cash_effect(transaction_type, data.quantity, data.price, data.fees)
    _apply_cash_delta(db, broker_account, new_cash_effect - old_cash_effect, user_id)
    record_finance_event(
        db, user_id=user_id, event_type="updated", entity_type="investment_transaction",
        entity_id=transaction_id, description="Investment transaction edited; broker cash reconciled",
        snapshot={"investment_id": existing.investment_id, "account_id": broker_account.id,
                  "old_cash_effect": old_cash_effect, "new_cash_effect": new_cash_effect},
    )
    db.commit()
    return dict(updated._mapping)


# ============================================================
# VOID TRANSACTION (AUDIT-PRESERVING; NOT HARD DELETE)
# ============================================================

@router.post("/{transaction_id}/void")
def void_transaction(
    transaction_id: int,
    data: InvestmentTransactionVoid,
    user_id: int | None = None,  # Legacy query parameter is ignored for security.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    ensure_transaction_table(db)
    # Resolve the parent investment first, then acquire the same parent-row
    # lock used by create_transaction. All ledger mutations for one investment
    # must serialize on this row before reading/validating the active timeline.
    locator = db.execute(text("""
        SELECT investment_id FROM investment_transactions
        WHERE id = :id AND user_id = :user_id
    """), {"id": transaction_id, "user_id": user_id}).first()
    if not locator:
        raise HTTPException(status_code=404, detail="Investment transaction not found.")

    locked_investment = db.execute(text("""
        SELECT id, investment_account_id FROM investments
        WHERE id = :investment_id AND user_id = :user_id
        FOR UPDATE
    """), {"investment_id": locator.investment_id, "user_id": user_id}).first()
    if not locked_investment:
        raise HTTPException(status_code=404, detail="Investment not found for this user.")

    existing = db.execute(text("""
        SELECT * FROM investment_transactions
        WHERE id = :id AND user_id = :user_id
        FOR UPDATE
    """), {"id": transaction_id, "user_id": user_id}).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Investment transaction not found.")
    if existing.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Transaction is already voided or inactive.")
    broker_account = _load_locked_broker_account(db, locked_investment, user_id)
    original_cash_effect = _cash_effect(
        existing.transaction_type, Decimal(str(existing.quantity)),
        Decimal(str(existing.price)), Decimal(str(existing.fees or 0)),
    )

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
    # Reverse the original trade cash movement; reject an overdrawn reversal atomically.
    _apply_cash_delta(db, broker_account, -original_cash_effect, user_id)
    record_finance_event(
        db, user_id=user_id, event_type="voided", entity_type="investment_transaction",
        entity_id=transaction_id, description="Investment transaction voided; broker cash reversed",
        snapshot={"investment_id": existing.investment_id, "account_id": broker_account.id,
                  "original_cash_effect": original_cash_effect, "reversal": -original_cash_effect,
                  "reason": data.reason.strip()},
    )
    db.commit()
    return {"status": "voided", "transaction_id": transaction_id, "reason": data.reason.strip(), "active_quantity": str(balance.quantity or 0)}


# ============================================================
# LEGACY DELETE ENDPOINT DISABLED TO PRESERVE AUDIT HISTORY
# ============================================================

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raise HTTPException(
        status_code=405,
        detail="Permanent deletion is disabled. Use POST /{transaction_id}/void with user_id and a reason to preserve audit history.",
    )
