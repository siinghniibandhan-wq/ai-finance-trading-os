from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import get_db


router = APIRouter(
    prefix="/api/liabilities",
    tags=["Liabilities"]
)


def ensure_liabilities_table(db: Session):
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS liabilities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                liability_type VARCHAR(100) NOT NULL DEFAULT 'other',
                institution VARCHAR(255),
                account_number VARCHAR(100),
                original_amount NUMERIC(14,2),
                outstanding_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
                interest_rate NUMERIC(8,4),
                monthly_emi NUMERIC(14,2),
                start_date DATE,
                due_date DATE,
                currency VARCHAR(10) NOT NULL DEFAULT 'INR',
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    db.commit()


class LiabilityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    liability_type: str = "other"
    institution: str | None = None
    account_number: str | None = None
    original_amount: float | None = None
    outstanding_amount: float = 0
    interest_rate: float | None = None
    monthly_emi: float | None = None
    start_date: date | None = None
    due_date: date | None = None
    currency: str = "INR"
    status: str = "active"
    notes: str | None = None


class LiabilityUpdate(LiabilityCreate):
    pass


def liability_row(row):
    return {
        "id": row.id,
        "name": row.name,
        "liability_type": row.liability_type,
        "institution": row.institution,
        "account_number": row.account_number,
        "original_amount": float(row.original_amount)
        if row.original_amount is not None
        else None,
        "outstanding_amount": float(row.outstanding_amount or 0),
        "interest_rate": float(row.interest_rate)
        if row.interest_rate is not None
        else None,
        "monthly_emi": float(row.monthly_emi)
        if row.monthly_emi is not None
        else None,
        "start_date": row.start_date.isoformat()
        if row.start_date
        else None,
        "due_date": row.due_date.isoformat()
        if row.due_date
        else None,
        "currency": row.currency,
        "status": row.status,
        "notes": row.notes,
        "created_at": row.created_at.isoformat()
        if row.created_at
        else None,
        "updated_at": row.updated_at.isoformat()
        if row.updated_at
        else None,
    }


@router.get("/")
def get_liabilities(db: Session = Depends(get_db)):
    ensure_liabilities_table(db)

    result = db.execute(
        text(
            """
            SELECT *
            FROM liabilities
            ORDER BY id DESC
            """
        )
    )

    return [liability_row(row) for row in result]


@router.get("/{liability_id}")
def get_liability(
    liability_id: int,
    db: Session = Depends(get_db)
):
    ensure_liabilities_table(db)

    result = db.execute(
        text(
            """
            SELECT *
            FROM liabilities
            WHERE id = :id
            """
        ),
        {"id": liability_id}
    )

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Liability not found."
        )

    return liability_row(row)


@router.post("/")
def create_liability(
    payload: LiabilityCreate,
    db: Session = Depends(get_db)
):
    ensure_liabilities_table(db)

    if payload.outstanding_amount < 0:
        raise HTTPException(
            status_code=400,
            detail="Outstanding amount cannot be negative."
        )

    result = db.execute(
        text(
            """
            INSERT INTO liabilities (
                name,
                liability_type,
                institution,
                account_number,
                original_amount,
                outstanding_amount,
                interest_rate,
                monthly_emi,
                start_date,
                due_date,
                currency,
                status,
                notes
            )
            VALUES (
                :name,
                :liability_type,
                :institution,
                :account_number,
                :original_amount,
                :outstanding_amount,
                :interest_rate,
                :monthly_emi,
                :start_date,
                :due_date,
                :currency,
                :status,
                :notes
            )
            RETURNING *
            """
        ),
        payload.model_dump()
    )

    db.commit()

    return liability_row(result.first())


@router.put("/{liability_id}")
def update_liability(
    liability_id: int,
    payload: LiabilityUpdate,
    db: Session = Depends(get_db)
):
    ensure_liabilities_table(db)

    existing = db.execute(
        text(
            """
            SELECT id
            FROM liabilities
            WHERE id = :id
            """
        ),
        {"id": liability_id}
    ).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Liability not found."
        )

    if payload.outstanding_amount < 0:
        raise HTTPException(
            status_code=400,
            detail="Outstanding amount cannot be negative."
        )

    result = db.execute(
        text(
            """
            UPDATE liabilities
            SET
                name = :name,
                liability_type = :liability_type,
                institution = :institution,
                account_number = :account_number,
                original_amount = :original_amount,
                outstanding_amount = :outstanding_amount,
                interest_rate = :interest_rate,
                monthly_emi = :monthly_emi,
                start_date = :start_date,
                due_date = :due_date,
                currency = :currency,
                status = :status,
                notes = :notes,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            RETURNING *
            """
        ),
        {
            **payload.model_dump(),
            "id": liability_id
        }
    )

    db.commit()

    return liability_row(result.first())


@router.delete("/{liability_id}")
def delete_liability(
    liability_id: int,
    db: Session = Depends(get_db)
):
    ensure_liabilities_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM liabilities
            WHERE id = :id
            RETURNING id
            """
        ),
        {"id": liability_id}
    )

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Liability not found."
        )

    db.commit()

    return {
        "message": "Liability deleted successfully.",
        "id": row.id
    }
