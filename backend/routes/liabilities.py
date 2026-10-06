# ============================================================
# LIABILITIES API ROUTES
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Liability
from database.schemas import (
    LiabilityCreate,
    LiabilityResponse,
    LiabilityUpdate,
)


# ============================================================
# ROUTER CONFIGURATION
# ============================================================

router = APIRouter(
    prefix="/api/liabilities",
    tags=["Liabilities"],
)


# ============================================================
# GET ALL LIABILITIES
# ============================================================

@router.get(
    "/",
    response_model=list[LiabilityResponse],
)
def get_liabilities(
    db: Session = Depends(get_db),
):
    """
    Return all active liabilities.
    """

    return (
        db.query(Liability)
        .filter(
            Liability.is_active.is_(True)
        )
        .order_by(
            Liability.id.desc()
        )
        .all()
    )


# ============================================================
# GET SINGLE LIABILITY
# ============================================================

@router.get(
    "/{liability_id}",
    response_model=LiabilityResponse,
)
def get_liability(
    liability_id: int,
    db: Session = Depends(get_db),
):
    """
    Return one active liability by ID.
    """

    liability = (
        db.query(Liability)
        .filter(
            Liability.id == liability_id,
            Liability.is_active.is_(True),
        )
        .first()
    )

    if not liability:
        raise HTTPException(
            status_code=404,
            detail="Liability not found",
        )

    return liability


# ============================================================
# CREATE LIABILITY
# ============================================================

@router.post(
    "/",
    response_model=LiabilityResponse,
    status_code=201,
)
def create_liability(
    data: LiabilityCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new liability.

    IMPORTANT:
    The field names below must match
    database.models.Liability exactly.
    """

    liability = Liability(
        name=data.name,
        liability_type=data.liability_type,
        lender=data.lender,

        # Correct database model field
        original_amount=data.original_amount,

        # Correct database model field
        outstanding_amount=data.outstanding_amount,

        interest_rate=data.interest_rate,

        # Correct database model field
        emi_amount=data.emi_amount,

        currency=data.currency,
        start_date=data.start_date,
        notes=data.notes,
    )

    db.add(liability)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(liability)

    return liability


# ============================================================
# UPDATE LIABILITY
# ============================================================

@router.put(
    "/{liability_id}",
    response_model=LiabilityResponse,
)
def update_liability(
    liability_id: int,
    data: LiabilityUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing active liability.
    """

    liability = (
        db.query(Liability)
        .filter(
            Liability.id == liability_id,
            Liability.is_active.is_(True),
        )
        .first()
    )

    if not liability:
        raise HTTPException(
            status_code=404,
            detail="Liability not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            liability,
            field,
            value,
        )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(liability)

    return liability


# ============================================================
# DELETE / ARCHIVE LIABILITY
# ============================================================

@router.delete(
    "/{liability_id}"
)
def archive_liability(
    liability_id: int,
    db: Session = Depends(get_db),
):
    """
    Soft-delete/archive a liability.

    The database record is retained.
    """

    liability = (
        db.query(Liability)
        .filter(
            Liability.id == liability_id,
            Liability.is_active.is_(True),
        )
        .first()
    )

    if not liability:
        raise HTTPException(
            status_code=404,
            detail="Liability not found",
        )

    liability.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Liability archived successfully",
        "liability_id": liability_id,
    }
