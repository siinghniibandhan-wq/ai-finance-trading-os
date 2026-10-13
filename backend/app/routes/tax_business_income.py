"""User-scoped business and professional tax records.
Records are self-reported and do not reduce taxable income until verified.
"""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import TaxBusinessIncomeRecord, Transaction, User
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
    source_transaction_id: int | None = Field(default=None, ge=1)

@router.post("/")
def create_record(payload: BusinessRecordIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    start_year = int(payload.financial_year[:4])
    end_short = int(payload.financial_year[5:])
    if end_short != (start_year + 1) % 100 or not 2000 <= start_year <= 2100:
        raise HTTPException(status_code=400, detail="Invalid Indian financial year.")
    if not (date(start_year, 4, 1) <= payload.transaction_date <= date(start_year + 1, 3, 31)):
        raise HTTPException(status_code=400, detail="Transaction date is outside the selected financial year.")
    source_transaction_id = payload.source_transaction_id
    if source_transaction_id is not None:
        source = db.query(Transaction).filter_by(id=source_transaction_id, user_id=current_user.id).first()
        if source is None:
            raise HTTPException(status_code=404, detail="Linked Money transaction was not found for this user.")
        if source.transaction_date != payload.transaction_date or Decimal(str(source.amount)) != payload.amount:
            raise HTTPException(status_code=400, detail="Linked transaction date and amount must match the tax record.")
        if payload.record_type == "receipt":
            if str(source.transaction_type or "").lower() != "income":
                raise HTTPException(status_code=400, detail="A business receipt must link to an income transaction, not interest or dividend.")
            from app.models import Category
            category = db.query(Category).filter_by(id=source.category_id).first() if source.category_id else None
            normalized_category = str(category.name if category else "").strip().lower()
            if normalized_category in {"salary", "salary & wages", "salaries", "loan disbursement"} or "gross salary:" in str(source.description or "").lower():
                raise HTTPException(status_code=400, detail="Salary and loan-disbursement transactions cannot be linked as business receipts.")
        if payload.record_type == "expense" and str(source.transaction_type or "").lower() != "expense":
            raise HTTPException(status_code=400, detail="An expense must link to an expense transaction.")
        existing_link = db.query(TaxBusinessIncomeRecord).filter_by(
            user_id=current_user.id, source_transaction_id=source_transaction_id
        ).first()
        if existing_link:
            raise HTTPException(status_code=409, detail="This Money transaction is already linked to a tax business record.")
    record = TaxBusinessIncomeRecord(user_id=current_user.id, financial_year=payload.financial_year,
        record_type=payload.record_type, income_type=payload.income_type, category=payload.category.strip(),
        amount=payload.amount, transaction_date=payload.transaction_date, description=payload.description,
        evidence_reference=payload.evidence_reference, source_transaction_id=source_transaction_id,
        status="pending_review")
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
            "evidence_reference": r.evidence_reference, "source_transaction_id": r.source_transaction_id, "status": r.status}
