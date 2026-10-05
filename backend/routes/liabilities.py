from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Liability
from database.schemas import (
    LiabilityCreate,
    LiabilityResponse,
    LiabilityUpdate,
)


router = APIRouter(
    prefix="/api/liabilities",
    tags=["Liabilities"],
)


@router.get("/", response_model=list[LiabilityResponse])
def get_liabilities(
    db: Session = Depends(get_db),
):
    return (
        db.query(Liability)
        .filter(Liability.is_active.is_(True))
        .order_by(Liability.id.desc())
        .all()
    )


@router.get(
    "/{liability_id}",
    response_model=LiabilityResponse,
)
def get_liability(
    liability_id: int,
    db: Session = Depends(get_db),
):
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


@router.post(
    "/",
    response_model=LiabilityResponse,
    status_code=201,
)
def create_liability(
    data: LiabilityCreate,
    db: Session = Depends(get_db),
):
    liability = Liability(
        name=data.name,
        liability_type=data.liability_type,
        lender=data.lender,
        principal_amount=data.principal_amount,
        outstanding_amount=data.outstanding_amount,
        interest_rate=data.interest_rate,
        monthly_emi=data.monthly_emi,
        currency=data.currency,
        start_date=data.start_date,
        notes=data.notes,
    )

    db.add(liability)
    db.commit()
    db.refresh(liability)

    return liability


@router.put(
    "/{liability_id}",
    response_model=LiabilityResponse,
)
def update_liability(
    liability_id: int,
    data: LiabilityUpdate,
    db: Session = Depends(get_db),
):
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
        setattr(liability, field, value)

    db.commit()
    db.refresh(liability)

    return liability


@router.delete("/{liability_id}")
def archive_liability(
    liability_id: int,
    db: Session = Depends(get_db),
):
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

    db.commit()

    return {
        "message": "Liability archived successfully",
        "liability_id": liability_id,
  }
