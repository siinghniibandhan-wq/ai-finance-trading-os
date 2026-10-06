# =====================================================
# AI FINANCE TRADING OS
# ASSETS BACKEND
# =====================================================
#
# PURPOSE:
# - Store personal wealth assets
# - Support multiple asset types
# - Support current value and purchase value
# - Allow Create / Read / Update / Delete
# - Keep this module isolated from Finance/Transactions
#
# IMPORTANT:
# - This module does NOT modify Transactions.
# - This module does NOT modify Accounts.
# - This module does NOT modify Statements.
# - Wealth calculations will use this data later.
# =====================================================


# =====================================================
# IMPORTS
# =====================================================

from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import get_db


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/assets",
    tags=["Wealth - Assets"]
)


# =====================================================
# DATABASE TABLE
# =====================================================

def ensure_assets_table(db: Session):
    """
    Create the assets table if it does not already exist.
    """

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id SERIAL PRIMARY KEY,

                name VARCHAR(255) NOT NULL,

                asset_type VARCHAR(100) NOT NULL,

                category VARCHAR(100) NULL,

                institution VARCHAR(255) NULL,

                quantity NUMERIC(18,6) NULL,

                purchase_value NUMERIC(18,2) NOT NULL DEFAULT 0,

                current_value NUMERIC(18,2) NOT NULL DEFAULT 0,

                purchase_date DATE NULL,

                currency VARCHAR(10) NOT NULL DEFAULT 'INR',

                notes TEXT NULL,

                status VARCHAR(50) NOT NULL DEFAULT 'active',

                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    db.commit()


# =====================================================
# PYDANTIC SCHEMAS
# =====================================================

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    asset_type: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    category: str | None = None

    institution: str | None = None

    quantity: Decimal | None = None

    purchase_value: Decimal = Field(
        default=Decimal("0")
    )

    current_value: Decimal = Field(
        default=Decimal("0")
    )

    purchase_date: date | None = None

    currency: str = "INR"

    notes: str | None = None

    status: str = "active"


class AssetUpdate(BaseModel):
    name: str | None = None

    asset_type: str | None = None

    category: str | None = None

    institution: str | None = None

    quantity: Decimal | None = None

    purchase_value: Decimal | None = None

    current_value: Decimal | None = None

    purchase_date: date | None = None

    currency: str | None = None

    notes: str | None = None

    status: str | None = None


# =====================================================
# VALIDATION HELPERS
# =====================================================

ALLOWED_STATUS = {
    "active",
    "inactive",
    "sold",
    "archived"
}


def validate_status(status: str):
    """
    Validate asset status.
    """

    if status not in ALLOWED_STATUS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid asset status. "
                "Allowed values: active, inactive, sold, archived."
            )
        )


def validate_decimal_values(
    purchase_value=None,
    current_value=None,
    quantity=None
):
    """
    Prevent negative financial values where inappropriate.
    """

    if purchase_value is not None and purchase_value < 0:
        raise HTTPException(
            status_code=400,
            detail="Purchase value cannot be negative."
        )

    if current_value is not None and current_value < 0:
        raise HTTPException(
            status_code=400,
            detail="Current value cannot be negative."
        )

    if quantity is not None and quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative."
        )


# =====================================================
# GET ALL ASSETS
# =====================================================

@router.get("/")
def get_assets(
    status: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Return all assets.

    Optional:
    ?status=active
    """

    ensure_assets_table(db)

    if status is not None:
        validate_status(status)

    if status:
        result = db.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    asset_type,
                    category,
                    institution,
                    quantity,
                    purchase_value,
                    current_value,
                    purchase_date,
                    currency,
                    notes,
                    status,
                    created_at,
                    updated_at
                FROM assets
                WHERE status = :status
                ORDER BY id DESC
                """
            ),
            {
                "status": status
            }
        )
    else:
        result = db.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    asset_type,
                    category,
                    institution,
                    quantity,
                    purchase_value,
                    current_value,
                    purchase_date,
                    currency,
                    notes,
                    status,
                    created_at,
                    updated_at
                FROM assets
                ORDER BY id DESC
                """
            )
        )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


# =====================================================
# GET SINGLE ASSET
# =====================================================

@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """
    Return one asset by ID.
    """

    ensure_assets_table(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                name,
                asset_type,
                category,
                institution,
                quantity,
                purchase_value,
                current_value,
                purchase_date,
                currency,
                notes,
                status,
                created_at,
                updated_at
            FROM assets
            WHERE id = :asset_id
            """
        ),
        {
            "asset_id": asset_id
        }
    )

    asset = result.mappings().first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found."
        )

    return dict(asset)


# =====================================================
# CREATE ASSET
# =====================================================

@router.post("/")
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new asset.
    """

    ensure_assets_table(db)

    validate_status(payload.status)

    validate_decimal_values(
        purchase_value=payload.purchase_value,
        current_value=payload.current_value,
        quantity=payload.quantity
    )

    result = db.execute(
        text(
            """
            INSERT INTO assets (
                name,
                asset_type,
                category,
                institution,
                quantity,
                purchase_value,
                current_value,
                purchase_date,
                currency,
                notes,
                status
            )
            VALUES (
                :name,
                :asset_type,
                :category,
                :institution,
                :quantity,
                :purchase_value,
                :current_value,
                :purchase_date,
                :currency,
                :notes,
                :status
            )
            RETURNING id
            """
        ),
        {
            "name": payload.name.strip(),
            "asset_type": payload.asset_type.strip(),
            "category": payload.category,
            "institution": payload.institution,
            "quantity": payload.quantity,
            "purchase_value": payload.purchase_value,
            "current_value": payload.current_value,
            "purchase_date": payload.purchase_date,
            "currency": payload.currency or "INR",
            "notes": payload.notes,
            "status": payload.status
        }
    )

    asset_id = result.scalar_one()

    db.commit()

    return {
        "success": True,
        "message": "Asset created successfully.",
        "asset_id": asset_id
    }


# =====================================================
# UPDATE ASSET
# =====================================================

@router.put("/{asset_id}")
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing asset.
    """

    ensure_assets_table(db)

    existing = db.execute(
        text(
            """
            SELECT id
            FROM assets
            WHERE id = :asset_id
            """
        ),
        {
            "asset_id": asset_id
        }
    ).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Asset not found."
        )

    if payload.status is not None:
        validate_status(payload.status)

    validate_decimal_values(
        purchase_value=payload.purchase_value,
        current_value=payload.current_value,
        quantity=payload.quantity
    )

    db.execute(
        text(
            """
            UPDATE assets
            SET
                name = COALESCE(:name, name),
                asset_type = COALESCE(:asset_type, asset_type),
                category = COALESCE(:category, category),
                institution = COALESCE(:institution, institution),
                quantity = COALESCE(:quantity, quantity),
                purchase_value = COALESCE(
                    :purchase_value,
                    purchase_value
                ),
                current_value = COALESCE(
                    :current_value,
                    current_value
                ),
                purchase_date = COALESCE(
                    :purchase_date,
                    purchase_date
                ),
                currency = COALESCE(:currency, currency),
                notes = COALESCE(:notes, notes),
                status = COALESCE(:status, status),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :asset_id
            """
        ),
        {
            "asset_id": asset_id,
            "name": payload.name,
            "asset_type": payload.asset_type,
            "category": payload.category,
            "institution": payload.institution,
            "quantity": payload.quantity,
            "purchase_value": payload.purchase_value,
            "current_value": payload.current_value,
            "purchase_date": payload.purchase_date,
            "currency": payload.currency,
            "notes": payload.notes,
            "status": payload.status
        }
    )

    db.commit()

    return {
        "success": True,
        "message": "Asset updated successfully.",
        "asset_id": asset_id
    }


# =====================================================
# DELETE ASSET
# =====================================================

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete an asset.
    """

    ensure_assets_table(db)

    result = db.execute(
        text(
            """
            DELETE FROM assets
            WHERE id = :asset_id
            RETURNING id
            """
        ),
        {
            "asset_id": asset_id
        }
    )

    deleted_id = result.scalar()

    if deleted_id is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found."
        )

    db.commit()

    return {
        "success": True,
        "message": "Asset deleted successfully.",
        "asset_id": deleted_id
    }
