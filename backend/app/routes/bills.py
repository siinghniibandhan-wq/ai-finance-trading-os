# =====================================================
# BILLS & SUBSCRIPTIONS API — USER-SCOPED
# =====================================================
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, Category, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/bills", tags=["Bills & Subscriptions"])


def ensure_bills_table(db: Session) -> None:
    """Create/upgrade the legacy bills table without dropping existing rows."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS bills (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category_id INTEGER NULL,
            account_id INTEGER NULL,
            amount NUMERIC(14,2) NOT NULL,
            frequency VARCHAR(50) NOT NULL,
            next_due_date DATE NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'active',
            notes TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NULL REFERENCES users(id) ON DELETE CASCADE
        )
    """))
    # Existing installations may already have a bills table without user_id.
    db.execute(text("""
        ALTER TABLE bills
        ADD COLUMN IF NOT EXISTS user_id INTEGER NULL REFERENCES users(id) ON DELETE CASCADE
    """))
    # Safe, idempotent legacy migration:
    # - If there is exactly one user, attach old bills to that user.
    # - If multiple users exist, quarantine legacy unowned bills under ADMIN_EMAIL.
    # - If no configured admin exists, leave legacy rows unowned/inaccessible rather
    #   than exposing them to every customer.
    user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
    if user_count == 1:
        sole_user_id = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).scalar_one()
        db.execute(
            text("UPDATE bills SET user_id = :user_id WHERE user_id IS NULL"),
            {"user_id": sole_user_id},
        )
    elif user_count > 1:
        import os
        admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        if admin_email:
            admin_id = db.execute(
                text("SELECT id FROM users WHERE lower(email) = :email LIMIT 1"),
                {"email": admin_email},
            ).scalar()
            if admin_id is not None:
                db.execute(
                    text("UPDATE bills SET user_id = :user_id WHERE user_id IS NULL"),
                    {"user_id": admin_id},
                )
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_bills_user_id ON bills(user_id)"))
    db.commit()


class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category_id: int | None = None
    account_id: int | None = None
    amount: Decimal = Field(gt=0)
    frequency: str = Field(min_length=1, max_length=50)
    next_due_date: date
    status: str = Field(default="active", max_length=30)
    notes: str | None = None


class BillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category_id: int | None = None
    account_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    frequency: str | None = Field(default=None, min_length=1, max_length=50)
    next_due_date: date | None = None
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None


ALLOWED_FREQUENCIES = {"daily", "weekly", "monthly", "quarterly", "half_yearly", "yearly", "custom"}
ALLOWED_STATUSES = {"active", "paused", "cancelled"}
RETURN_COLUMNS = """
    id, name, category_id, account_id, amount, frequency,
    next_due_date, status, notes, created_at, updated_at
"""


def validate_frequency(frequency: str) -> None:
    if frequency not in ALLOWED_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Invalid frequency. Use daily, weekly, monthly, quarterly, half_yearly, yearly or custom.")


def validate_status(status: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status. Use active, paused or cancelled.")


def validate_category(db: Session, category_id: int | None, user_id: int) -> None:
    if category_id is None:
        return
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")


def validate_account(db: Session, account_id: int | None, user_id: int) -> None:
    if account_id is None:
        return
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id,
        Account.is_active.is_(True),
    ).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")


@router.get("/")
def get_bills(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_bills_table(db)
    if status is not None:
        validate_status(status)
    query = f"SELECT {RETURN_COLUMNS} FROM bills WHERE user_id = :user_id"
    params = {"user_id": current_user.id}
    if status is not None:
        query += " AND status = :status"
        params["status"] = status
    query += " ORDER BY next_due_date ASC, id DESC"
    rows = db.execute(text(query), params)
    return [dict(row._mapping) for row in rows]


@router.get("/{bill_id}")
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_bills_table(db)
    row = db.execute(
        text(f"SELECT {RETURN_COLUMNS} FROM bills WHERE id = :bill_id AND user_id = :user_id"),
        {"bill_id": bill_id, "user_id": current_user.id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return dict(row._mapping)


@router.post("/", status_code=201)
def create_bill(
    data: BillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_bills_table(db)
    validate_frequency(data.frequency)
    validate_status(data.status)
    validate_category(db, data.category_id, current_user.id)
    validate_account(db, data.account_id, current_user.id)
    row = db.execute(text("""
        INSERT INTO bills (
            user_id, name, category_id, account_id, amount, frequency,
            next_due_date, status, notes
        ) VALUES (
            :user_id, :name, :category_id, :account_id, :amount, :frequency,
            :next_due_date, :status, :notes
        )
        RETURNING id, name, category_id, account_id, amount, frequency,
                  next_due_date, status, notes, created_at, updated_at
    """), {
        "user_id": current_user.id,
        "name": data.name.strip(),
        "category_id": data.category_id,
        "account_id": data.account_id,
        "amount": data.amount,
        "frequency": data.frequency,
        "next_due_date": data.next_due_date,
        "status": data.status,
        "notes": data.notes,
    }).first()
    db.commit()
    return dict(row._mapping)


@router.put("/{bill_id}")
def update_bill(
    bill_id: int,
    data: BillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_bills_table(db)
    existing = db.execute(
        text("SELECT id FROM bills WHERE id = :bill_id AND user_id = :user_id"),
        {"bill_id": bill_id, "user_id": current_user.id},
    ).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    if "frequency" in update_data and update_data["frequency"] is not None:
        validate_frequency(update_data["frequency"])
    if "status" in update_data and update_data["status"] is not None:
        validate_status(update_data["status"])
    if "category_id" in update_data:
        validate_category(db, update_data["category_id"], current_user.id)
    if "account_id" in update_data:
        validate_account(db, update_data["account_id"], current_user.id)

    allowed_fields = {"name", "category_id", "account_id", "amount", "frequency", "next_due_date", "status", "notes"}
    set_parts = []
    params = {"bill_id": bill_id, "user_id": current_user.id}
    for field, value in update_data.items():
        if field not in allowed_fields:
            continue
        set_parts.append(f"{field} = :{field}")
        params[field] = value.strip() if field == "name" and isinstance(value, str) else value
    if not set_parts:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    row = db.execute(text(f"""
        UPDATE bills SET {", ".join(set_parts)}
        WHERE id = :bill_id AND user_id = :user_id
        RETURNING id, name, category_id, account_id, amount, frequency,
                  next_due_date, status, notes, created_at, updated_at
    """), params).first()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Bill not found")
    db.commit()
    return dict(row._mapping)


@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_bills_table(db)
    row = db.execute(
        text("DELETE FROM bills WHERE id = :bill_id AND user_id = :user_id RETURNING id"),
        {"bill_id": bill_id, "user_id": current_user.id},
    ).first()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Bill not found")
    db.commit()
    return {"message": "Bill deleted successfully", "bill_id": bill_id}
