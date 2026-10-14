"""User-scoped house property income records.

A record is saved as pending review and counts in taxable income only after
the owner verifies it with an evidence reference. The app does not inspect
documents. Money rent receipts are never converted into records automatically.
"""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.house_property_calc import PROPERTY_TYPES, compute_house_property
from app.models import TaxHousePropertyRecord, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/tax-house-property", tags=["Tax House Property"])


class HousePropertyIn(BaseModel):
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    property_type: str = Field(pattern=r"^(let_out|self_occupied|none)$")
    property_label: str | None = Field(default=None, max_length=120)
    annual_rent_received: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    municipal_taxes_paid: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    interest_on_housing_loan: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)


class HousePropertyAction(BaseModel):
    evidence_reference: str | None = Field(default=None, max_length=1000)


def _summary(record, tax_regime="old"):
    estimate = compute_house_property([record], tax_regime)["properties"][0]["income"] if record.property_type in PROPERTY_TYPES else Decimal("0")
    return {
        "id": record.id, "financial_year": record.financial_year,
        "property_type": record.property_type, "property_label": record.property_label,
        "annual_rent_received": str(record.annual_rent_received),
        "municipal_taxes_paid": str(record.municipal_taxes_paid),
        "interest_on_housing_loan": str(record.interest_on_housing_loan),
        "evidence_reference": record.evidence_reference, "status": record.status,
        "counted_as_verified": record.status == "verified",
        "estimated_income_old_regime": str(estimate),
    }


def _owned(db, record_id, user_id):
    record = db.query(TaxHousePropertyRecord).filter_by(id=record_id, user_id=user_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="House property record not found.")
    return record


@router.post("/", status_code=201)
def create_house_property_record(payload: HousePropertyIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save a self-reported record as pending. It does not affect tax until verified."""
    is_none = payload.property_type == "none"
    record = TaxHousePropertyRecord(
        user_id=current_user.id, financial_year=payload.financial_year,
        property_type=payload.property_type,
        property_label=(payload.property_label or "").strip() or None,
        annual_rent_received=Decimal("0") if is_none else payload.annual_rent_received,
        municipal_taxes_paid=Decimal("0") if is_none else payload.municipal_taxes_paid,
        interest_on_housing_loan=Decimal("0") if is_none else payload.interest_on_housing_loan,
        status="pending_review",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _summary(record)


@router.get("/")
def list_house_property_records(financial_year: str = Query("2026-27", pattern=r"^\d{4}-\d{2}$"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (
        db.query(TaxHousePropertyRecord)
        .filter_by(user_id=current_user.id, financial_year=financial_year)
        .order_by(TaxHousePropertyRecord.id.desc())
        .all()
    )
    return {"financial_year": financial_year, "entries": [_summary(r) for r in records]}


@router.post("/{record_id}/verify")
def verify_house_property_record(record_id: int, payload: HousePropertyAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = _owned(db, record_id, current_user.id)
    reference = (payload.evidence_reference or record.evidence_reference or "").strip()
    if len(reference) < 3:
        raise HTTPException(status_code=400, detail="Enter an evidence reference (for example rent agreement or loan interest certificate) before verifying.")
    others = (
        db.query(TaxHousePropertyRecord)
        .filter(
            TaxHousePropertyRecord.user_id == current_user.id,
            TaxHousePropertyRecord.financial_year == record.financial_year,
            TaxHousePropertyRecord.status == "verified",
            TaxHousePropertyRecord.id != record.id,
        )
        .all()
    )
    if record.property_type == "none" and others:
        raise HTTPException(status_code=409, detail="You have other verified house property records. Set them back to pending before confirming that you have none.")
    if record.property_type != "none" and any(o.property_type == "none" for o in others):
        raise HTTPException(status_code=409, detail="You have confirmed 'no house property'. Set that record back to pending before verifying a property.")
    record.evidence_reference = reference
    record.status = "verified"
    db.commit()
    db.refresh(record)
    result = _summary(record)
    result["message"] = "Marked verified on your confirmation. Keep the supporting documents; this app does not check them."
    return result


@router.post("/{record_id}/unverify")
def unverify_house_property_record(record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = _owned(db, record_id, current_user.id)
    record.status = "pending_review"
    db.commit()
    db.refresh(record)
    result = _summary(record)
    result["message"] = "Returned to pending review. It no longer affects taxable income."
    return result


@router.delete("/{record_id}")
def delete_house_property_record(record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = _owned(db, record_id, current_user.id)
    db.delete(record)
    db.commit()
    return {"id": record_id, "deleted": True}
