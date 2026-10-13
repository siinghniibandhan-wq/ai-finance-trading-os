"""User-scoped business and professional tax records.
Records are self-reported and do not reduce taxable income until verified.
"""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import TaxBusinessIncomeRecord, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/tax-business-income", tags=["Tax Business Income"])

class BusinessRecordIn(BaseModel):
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    record_type: str = Field(pattern=r"^(receipt|expense)$")
    income_type: str = Field(pattern=r"^(business|profession|freelance)$")
    category: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    transaction_date: date
    description: str | None = Field(default=None, max_length=2000)
    evidence_reference: str | None = Field(default=None, max_length=1000)

@router.post("/")
def create_record(payload: BusinessRecordIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    start_year = int(payload.financial_year[:4])
    end_short = int(payload.financial_year[5:])
    if end_short != (start_year + 1) % 100 or not 2000 <= start_year <= 2100:
        raise HTTPException(status_code=400, detail="Invalid Indian financial year.")
    if not (date(start_year, 4, 1) <= payload.transaction_date <= date(start_year + 1, 3, 31)):
        raise HTTPException(status_code=400, detail="Transaction date is outside the selected financial year.")
    record = TaxBusinessIncomeRecord(user_id=current_user.id, financial_year=payload.financial_year,
        record_type=payload.record_type, income_type=payload.income_type, category=payload.category.strip(),
        amount=payload.amount, transaction_date=payload.transaction_date, description=payload.description,
        evidence_reference=payload.evidence_reference, status="pending_review")
    db.add(record); db.commit(); db.refresh(record)
    return _serialize(record)

@router.get("/")
def list_records(financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(TaxBusinessIncomeRecord).filter_by(user_id=current_user.id, financial_year=financial_year).order_by(TaxBusinessIncomeRecord.transaction_date.desc(), TaxBusinessIncomeRecord.id.desc()).all()
    receipts = sum((r.amount for r in records if r.record_type == "receipt" and r.status == "verified"), Decimal("0"))
    expenses = sum((r.amount for r in records if r.record_type == "expense" and r.status == "verified"), Decimal("0"))
    return {"financial_year": financial_year, "records": [_serialize(r) for r in records],
            "verified_gross_receipts": str(receipts), "verified_expenses": str(expenses),
            "provisional_verified_profit": str(receipts-expenses),
            "note": "Self-reported records remain pending review by default. This summary is not a final tax computation."}

def _serialize(r):
    return {"id": r.id, "financial_year": r.financial_year, "record_type": r.record_type,
            "income_type": r.income_type, "category": r.category, "description": r.description,
            "amount": str(r.amount), "transaction_date": r.transaction_date.isoformat(),
            "evidence_reference": r.evidence_reference, "status": r.status}
