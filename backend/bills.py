# =====================================================
# BILLS & SUBSCRIPTIONS API
# AI FINANCE TRADING OS
# =====================================================

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Account, Category


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/bills",
    tags=["Bills & Subscriptions"],
)


# =====================================================
# DATABASE TABLE
# =====================================================

def ensure_bills_table(db: Session):
    """
    Create the bills table if it does not already exist.
    This keeps Bills independent from the existing
    transaction/category/account tables.
    """

    db.execute(
        text(
            """
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

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    db.commit()


# =====================================================
# PYDANTIC SCHEMAS
# =====================================================

class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    category_id: int | None = None

    account_id: int | None = None

    amount: Decimal = Field(gt=0)

    frequency: str = Field(
        min_length=1,
        max_length=50
    )

    next_due_date: date

    status: str = Field(
        default="active",
        max_length=30
    )

    notes: str | None = None


class BillUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    category_id: int | None = None

    account_id: int | None = None

    amount: Decimal | None = Field(
        default=None,
        gt=0
    )

    frequency: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    next_due_date: date | None = None

    status: str | None = Field(
        default=None,
        max_length=30
    )

    notes: str | None = None


# =====================================================
# VALIDATION HELPERS
# =====================================================

ALLOWED_FREQUENCIES = {
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "half_yearly",
    "yearly",
    "custom",
}


ALLOWED_STATUSES = {
    "active",
    "paused",
    "cancelled",
}


def validate_frequency(frequency: str):
    if frequency not in ALLOWED_FREQUENCIES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid frequency. "
                "Use daily, weekly, monthly, quarterly, "
                "half_yearly, yearly or custom."
            ),
        )


def validate_status(status: str):
    if status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use active, paused or cancelled."
            ),
        )


def validate_category(
    db: Session,
    category_id: int | None,
):
    if category_id is None:
        return

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )


def validate_account(
    db: Session,
    account_id: int | None,
):
    if account_id is None:
        return

    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )


# =====================================================
# GET ALL BILLS
# =====================================================

@router.get("/")
def get_bills(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    ensure_bills_table(db)

    if status is not None:
        validate_status(status)

    query = """
        SELECT
            id,
            name,
            category_id,
            account_id,
            amount,
            frequency,
            next_due_date,
            status,
            notes,
            created_at,
            updated_at
        FROM bills
    """

    params = {}

    if status is not None:
        query += " WHERE status = :status"
        params["status"] = status

    query += """
        ORDER BY next_due_date ASC, id DESC
    """

    result = db.execute(
        text(query),
        params,
    )

    return [
        dict(row._mapping)
        for row in result
    ]


# =====================================================
# GET SINGLE BILL
# =====================================================

@router.get("/{bill_id}")
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
):
    ensure_bills_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                name,
                category_id,
                account_id,
                amount,
                frequency,
                next_due_date,
                status,
                notes,
                created_at,
                updated_at
            FROM bills
            WHERE id = :bill_id
            """
        ),
        {
            "bill_id": bill_id
        },
    ).first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Bill not found",
        )

    return dict(result._mapping)


# =====================================================
# CREATE BILL
# =====================================================

@router.post("/", status_code=201)
def create_bill(
    data: BillCreate,
    db: Session = Depends(get_db),
):
    ensure_bills_table(db)

    validate_frequency(data.frequency)
    validate_status(data.status)

    validate_category(
        db,
        data.category_id,
    )

    validate_account(
        db,
        data.account_id,
    )

    result = db.execute(
        text(
            """
            INSERT INTO bills (
                name,
                category_id,
                account_id,
                amount,
                frequency,
                next_due_date,
                status,
                notes
            )
            VALUES (
                :name,
                :category_id,
                :account_id,
                :amount,
                :frequency,
                :next_due_date,
                :status,
                :notes
            )
            RETURNING
                id,
                name,
                category_id,
                account_id,
                amount,
                frequency,
                next_due_date,
                status,
                notes,
                created_at,
                updated_at
            """
        ),
        {
            "name": data.name.strip(),
            "category_id": data.category_id,
            "account_id": data.account_id,
            "amount": data.amount,
            "frequency": data.frequency,
            "next_due_date": data.next_due_date,
            "status": data.status,
            "notes": data.notes,
        },
    )

    db.commit()

    row = result.first()

    return dict(row._mapping)


# =====================================================
# UPDATE BILL
# =====================================================

@router.put("/{bill_id}")
def update_bill(
    bill_id: int,
    data: BillUpdate,
    db: Session = Depends(get_db),
):
    ensure_bills_table(db)

    existing = db.execute(
        text(
            """
            SELECT *
            FROM bills
            WHERE id = :bill_id
            """
        ),
        {
            "bill_id": bill_id
        },
    ).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Bill not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    if "frequency" in update_data:
        validate_frequency(
            update_data["frequency"]
        )

    if "status" in update_data:
        validate_status(
            update_data["status"]
        )

    if "category_id" in update_data:
        validate_category(
            db,
            update_data["category_id"]
        )

    if "account_id" in update_data:
        validate_account(
            db,
            update_data["account_id"]
        )

    allowed_fields = {
        "name",
        "category_id",
        "account_id",
        "amount",
        "frequency",
        "next_due_date",
        "status",
        "notes",
    }

    set_parts = []
    params = {
        "bill_id": bill_id
    }

    for field, value in update_data.items():

        if field not in allowed_fields:
            continue

        set_parts.append(
            f"{field} = :{field}"
        )

        if field == "name" and isinstance(value, str):
            value = value.strip()

        params[field] = value

    set_parts.append(
        "updated_at = CURRENT_TIMESTAMP"
    )

    query = f"""
        UPDATE bills
        SET {", ".join(set_parts)}
        WHERE id = :bill_id
        RETURNING
            id,
            name,
            category_id,
            account_id,
            amount,
            frequency,
            next_due_date,
            status,
            notes,
            created_at,
            updated_at
    """

    result = db.execute(
        text(query),
        params,
    )

    db.commit()

    row = result.first()

    return dict(row._mapping)


# =====================================================
# DELETE BILL
# =====================================================

@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
):
    ensure_bills_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM bills
            WHERE id = :bill_id
            RETURNING id
            """
        ),
        {
            "bill_id": bill_id
        },
    )

    db.commit()

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Bill not found",
        )

    return {
        "message": "Bill deleted successfully",
        "bill_id": bill_id,
    }
