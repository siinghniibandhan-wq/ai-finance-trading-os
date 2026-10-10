# ============================================================
# FINANCIAL OS - LOANS & LIABILITIES API (FOUNDATION)
# This stage manages loan/liability records only. Transaction
# disbursement and repayment automation is a later integration.
# ============================================================
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, Liability, Loan, User

router = APIRouter(tags=["Loans & Liabilities"])

class LoanPayload(BaseModel):
    user_id: int = 1
    name: str = Field(min_length=1, max_length=150)
    lender_name: str = Field(min_length=1, max_length=150)
    loan_type: str = Field(min_length=1, max_length=60)
    principal_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    amount_disbursed: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    deposit_account_id: Optional[int] = None
    interest_rate: Optional[Decimal] = Field(default=None, ge=0, le=100, max_digits=7, decimal_places=4)
    interest_type: str = "reducing_balance"
    tenure_months: Optional[int] = Field(default=None, gt=0, le=600)
    emi_amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    start_date: date
    first_payment_date: Optional[date] = None
    repayment_frequency: str = "monthly"
    processing_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class LiabilityPayload(BaseModel):
    user_id: int = 1
    name: str = Field(min_length=1, max_length=150)
    liability_type: str = "other"
    original_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    outstanding_amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    due_date: Optional[date] = None
    notes: Optional[str] = None

def _loan_dict(x: Loan):
    return {"id": x.id, "user_id": x.user_id, "name": x.name, "lender_name": x.lender_name, "loan_type": x.loan_type, "principal_amount": float(x.principal_amount), "amount_disbursed": float(x.amount_disbursed), "outstanding_principal": float(x.outstanding_principal), "deposit_account_id": x.deposit_account_id, "interest_rate": float(x.interest_rate) if x.interest_rate is not None else None, "interest_type": x.interest_type, "tenure_months": x.tenure_months, "emi_amount": float(x.emi_amount) if x.emi_amount is not None else None, "start_date": x.start_date.isoformat(), "first_payment_date": x.first_payment_date.isoformat() if x.first_payment_date else None, "repayment_frequency": x.repayment_frequency, "processing_fee": float(x.processing_fee or 0), "reference_number": x.reference_number, "notes": x.notes, "status": x.status, "liability_id": x.liability.id if x.liability else None}

def _liability_dict(x: Liability):
    return {"id": x.id, "user_id": x.user_id, "name": x.name, "liability_type": x.liability_type, "original_amount": float(x.original_amount), "outstanding_amount": float(x.outstanding_amount), "loan_id": x.loan_id, "due_date": x.due_date.isoformat() if x.due_date else None, "notes": x.notes, "status": x.status}

@router.get("/api/loans")
def list_loans(user_id: int = Query(default=1, ge=1), db: Session = Depends(get_db)):
    items = db.query(Loan).filter(Loan.user_id == user_id).order_by(Loan.created_at.desc()).all()
    return {"status": "success", "loans": [_loan_dict(x) for x in items]}

@router.post("/api/loans")
def create_loan(payload: LoanPayload, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == payload.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if payload.amount_disbursed > payload.principal_amount:
        raise HTTPException(status_code=400, detail="Amount disbursed cannot exceed principal amount")
    if payload.deposit_account_id is not None and not db.query(Account).filter(Account.id == payload.deposit_account_id, Account.user_id == payload.user_id).first():
        raise HTTPException(status_code=404, detail="Deposit account not found for this user")
    try:
        loan = Loan(**payload.model_dump(), outstanding_principal=payload.principal_amount)
        db.add(loan); db.flush()
        liability = Liability(user_id=payload.user_id, name=payload.name, liability_type=payload.loan_type, original_amount=payload.principal_amount, outstanding_amount=payload.principal_amount, loan_id=loan.id)
        db.add(liability); db.commit(); db.refresh(loan)
        return {"status": "success", "loan": _loan_dict(loan)}
    except Exception:
        db.rollback()
        raise

@router.get("/api/liabilities")
def list_liabilities(user_id: int = Query(default=1, ge=1), db: Session = Depends(get_db)):
    items = db.query(Liability).filter(Liability.user_id == user_id).order_by(Liability.created_at.desc()).all()
    return {"status": "success", "liabilities": [_liability_dict(x) for x in items], "total_outstanding": float(sum((x.outstanding_amount for x in items if x.status == "active"), Decimal("0")))}

@router.post("/api/liabilities")
def create_liability(payload: LiabilityPayload, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == payload.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if payload.outstanding_amount > payload.original_amount:
        raise HTTPException(status_code=400, detail="Outstanding amount cannot exceed original amount")
    item = Liability(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return {"status": "success", "liability": _liability_dict(item)}
