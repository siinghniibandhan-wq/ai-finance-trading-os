from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Asset
from database.schemas import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)


router = APIRouter(
    prefix="/api/assets",
    tags=["Assets"],
)


@router.get("/", response_model=list[AssetResponse])
def get_assets(
    db: Session = Depends(get_db),
):
    return (
        db.query(Asset)
        .filter(Asset.is_active.is_(True))
        .order_by(Asset.id.desc())
        .all()
    )


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.is_active.is_(True),
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return asset


@router.post(
    "/",
    response_model=AssetResponse,
    status_code=201,
)
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
):
    asset = Asset(
        name=data.name,
        asset_type=data.asset_type,
        institution=data.institution,
        quantity=data.quantity,
        purchase_value=data.purchase_value,
        current_value=data.current_value,
        currency=data.currency,
        purchase_date=data.purchase_date,
        notes=data.notes,
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


@router.put(
    "/{asset_id}",
    response_model=AssetResponse,
)
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.is_active.is_(True),
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    return asset


@router.delete("/{asset_id}")
def archive_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.is_active.is_(True),
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    asset.is_active = False

    db.commit()

    return {
        "message": "Asset archived successfully",
        "asset_id": asset_id,
      }
