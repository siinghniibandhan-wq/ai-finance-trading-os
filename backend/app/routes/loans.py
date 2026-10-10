# ============================================================
# FINANCIAL OS - LOANS, LIABILITIES & LOAN RECEIVABLES
# Transaction-linked loan operations. Each cash movement creates
# one transaction and one LoanMovement in the same DB commit.
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import (
    Account, Liability, Loan, LoanMovement, LoanReceivable,
    Transaction, User,
)

router = APIRouter(tags=["Loans & Liabilities"])


# ============================================================
# REQUEST SCHEMAS
# ============================================================

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


class LoanReceivableCreate(BaseModel):
    user_id: int = 1
    source_account_id: int
    borrower_name: str = Field(min_length=1, max_length=150)
    name: str = Field(min_length=1, max_length=150)
    principal_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    interest_rate: Optional[Decimal] = Field(default=None, ge=0, le=100, max_digits=7, decimal_places=4)
    start_date: date
    due_date: Optional[date] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class LoanMovementCreate(BaseModel):
    user_id: int = 1
    account_id: int
    principal_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    interest_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    fee_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    transaction_date: date
    reference: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# RESPONSE HELPERS
# ============================================================

def _loan_dict(x: Loan):
    return {
        "id": x.id, "user_id": x.user_id, "name": x.name,
        "lender_name": x.lender_name, "loan_type": x.loan_type,
        "principal_amount": float(x.principal_amount),
        "amount_disbursed": float(x.amount_disbursed),
        "outstanding_principal": float(x.outstanding_principal),
        "deposit_account_id": x.deposit_account_id,
        "interest_rate": float(x.interest_rate) if x.interest_rate is not None else None,
        "interest_type": x.interest_type, "tenure_months": x.tenure_months,
        "emi_amount": float(x.emi_amount) if x.emi_amount is not None else None,
        "start_date": x.start_date.isoformat(),
        "first_payment_date": x.first_payment_date.isoformat() if x.first_payment_date else None,
        "repayment_frequency": x.repayment_frequency,
        "processing_fee": float(x.processing_fee or 0),
        "reference_number": x.reference_number, "notes": x.notes,
        "status": x.status, "liability_id": x.liability.id if x.liability else None,
    }


def _liability_dict(x: Liability):
    return {
        "id": x.id, "user_id": x.user_id, "name": x.name,
        "liability_type": x.liability_type,
        "original_amount": float(x.original_amount),
        "outstanding_amount": float(x.outstanding_amount),
        "loan_id": x.loan_id,
        "due_date": x.due_date.isoformat() if x.due_date else None,
        "notes": x.notes, "status": x.status,
    }


def _receivable_dict(x: LoanReceivable):
    return {
        "id": x.id, "user_id": x.user_id, "borrower_name": x.borrower_name,
        "name": x.name, "original_principal": float(x.original_principal),
        "outstanding_principal": float(x.outstanding_principal),
        "source_account_id": x.source_account_id,
        "disbursement_transaction_id": x.disbursement_transaction_id,
        "interest_rate": float(x.interest_rate) if x.interest_rate is not None else None,
        "start_date": x.start_date.isoformat(),
        "due_date": x.due_date.isoformat() if x.due_date else None,
        "reference_number": x.reference_number, "notes": x.notes,
        "status": x.status,
    }


def _movement_dict(x: LoanMovement):
    return {
        "id": x.id, "user_id": x.user_id, "loan_id": x.loan_id,
        "receivable_id": x.receivable_id, "transaction_id": x.transaction_id,
        "movement_type": x.movement_type,
        "principal_amount": float(x.principal_amount),
        "interest_amount": float(x.interest_amount),
        "fee_amount": float(x.fee_amount),
        "created_at": x.created_at.isoformat() if x.created_at else None,
    }


def _owned_account(db: Session, user_id: int, account_id: int, lock: bool = True):
    query = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id)
    if lock:
        query = query.with_for_update()
    account = query.first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found for this user")
    return account


def _owned_user(db: Session, user_id: int):
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")


# ============================================================
# LOAN RECEIVED (BORROWED MONEY)
# Existing transaction-based Loan Disbursement creation remains
# in transactions.py. This route adds principal/interest repayment.
# ============================================================

@router.get("/api/loans")
def list_loans(user_id: int = Query(default=1, ge=1), db: Session = Depends(get_db)):
    items = db.query(Loan).filter(Loan.user_id == user_id).order_by(Loan.created_at.desc()).all()
    return {"status": "success", "loans": [_loan_dict(x) for x in items]}


@router.post("/api/loans")
def create_loan(payload: LoanPayload, db: Session = Depends(get_db)):
    _owned_user(db, payload.user_id)
    if payload.amount_disbursed > payload.principal_amount:
        raise HTTPException(status_code=400, detail="Amount disbursed cannot exceed principal amount")
    if payload.deposit_account_id is not None:
        _owned_account(db, payload.user_id, payload.deposit_account_id, lock=False)
    try:
        loan = Loan(**payload.model_dump(), outstanding_principal=payload.principal_amount)
        db.add(loan)
        db.flush()
        liability = Liability(
            user_id=payload.user_id, name=payload.name,
            liability_type=payload.loan_type,
            original_amount=payload.principal_amount,
            outstanding_amount=payload.principal_amount, loan_id=loan.id,
        )
        db.add(liability)
        db.commit()
        db.refresh(loan)
        return {"status": "success", "loan": _loan_dict(loan)}
    except Exception:
        db.rollback()
        raise


@router.post("/api/loans/{loan_id}/repayments")
def repay_loan(loan_id: int, payload: LoanMovementCreate, db: Session = Depends(get_db)):
    """Record one cash repayment, splitting principal, interest and fees."""
    _owned_user(db, payload.user_id)
    total = payload.principal_amount + payload.interest_amount + payload.fee_amount
    if total <= 0:
        raise HTTPException(status_code=422, detail="Repayment total must be greater than zero")

    loan = (
        db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == payload.user_id)
        .with_for_update().first()
    )
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if payload.principal_amount > loan.outstanding_principal:
        raise HTTPException(status_code=422, detail="Principal repayment exceeds outstanding principal")
    account = _owned_account(db, payload.user_id, payload.account_id)
    liability = db.query(Liability).filter(Liability.loan_id == loan.id).with_for_update().first()

    try:
        tx = Transaction(
            user_id=payload.user_id, account_id=account.id, category_id=None,
            transaction_type="loan_repayment", amount=total,
            description=payload.notes or f"Loan repayment: {loan.name}",
            transaction_date=payload.transaction_date, reference=payload.reference,
        )
        db.add(tx)
        db.flush()
        movement = LoanMovement(
            user_id=payload.user_id, loan_id=loan.id, receivable_id=None,
            transaction_id=tx.id, movement_type="repayment",
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount, fee_amount=payload.fee_amount,
        )
        db.add(movement)
        loan.outstanding_principal -= payload.principal_amount
        loan.status = "closed" if loan.outstanding_principal == 0 else "active"
        if liability:
            liability.outstanding_amount = loan.outstanding_principal
            liability.status = "closed" if liability.outstanding_amount == 0 else "active"
        account.balance = (account.balance or Decimal("0")) - total
        db.commit()
        db.refresh(movement)
        return {"status": "success", "transaction_id": tx.id, "movement": _movement_dict(movement), "loan": _loan_dict(loan), "account_balance": float(account.balance)}
    except Exception:
        db.rollback()
        raise


# ============================================================
# LOAN GIVEN (RECEIVABLE ASSET)
# ============================================================

@router.get("/api/loan-receivables")
def list_loan_receivables(user_id: int = Query(default=1, ge=1), db: Session = Depends(get_db)):
    items = db.query(LoanReceivable).filter(LoanReceivable.user_id == user_id).order_by(LoanReceivable.created_at.desc()).all()
    return {"status": "success", "loan_receivables": [_receivable_dict(x) for x in items]}


@router.post("/api/loan-receivables")
def create_loan_receivable(payload: LoanReceivableCreate, db: Session = Depends(get_db)):
    """Disburse a loan to a borrower: cash decreases, receivable asset increases."""
    _owned_user(db, payload.user_id)
    account = _owned_account(db, payload.user_id, payload.source_account_id)
    if account.balance is not None and account.balance < payload.principal_amount:
        raise HTTPException(status_code=422, detail="Insufficient account balance for this loan disbursement")

    try:
        tx = Transaction(
            user_id=payload.user_id, account_id=account.id, category_id=None,
            transaction_type="withdrawal", amount=payload.principal_amount,
            description=f"Loan given to {payload.borrower_name}: {payload.name}",
            transaction_date=payload.start_date, reference=payload.reference_number,
        )
        db.add(tx)
        db.flush()
        receivable = LoanReceivable(
            user_id=payload.user_id, borrower_name=payload.borrower_name,
            name=payload.name, original_principal=payload.principal_amount,
            outstanding_principal=payload.principal_amount, source_account_id=account.id,
            disbursement_transaction_id=tx.id, interest_rate=payload.interest_rate,
            start_date=payload.start_date, due_date=payload.due_date,
            reference_number=payload.reference_number, notes=payload.notes, status="active",
        )
        db.add(receivable)
        db.flush()
        movement = LoanMovement(
            user_id=payload.user_id, loan_id=None, receivable_id=receivable.id,
            transaction_id=tx.id, movement_type="disbursement",
            principal_amount=payload.principal_amount,
            interest_amount=Decimal("0"), fee_amount=Decimal("0"),
        )
        db.add(movement)
        account.balance = (account.balance or Decimal("0")) - payload.principal_amount
        db.commit()
        db.refresh(receivable)
        return {"status": "success", "loan_receivable": _receivable_dict(receivable), "transaction_id": tx.id, "account_balance": float(account.balance)}
    except Exception:
        db.rollback()
        raise


@router.post("/api/loan-receivables/{receivable_id}/recoveries")
def recover_loan(receivable_id: int, payload: LoanMovementCreate, db: Session = Depends(get_db)):
    """Record cash received from a borrower; principal is not income."""
    _owned_user(db, payload.user_id)
    total = payload.principal_amount + payload.interest_amount + payload.fee_amount
    if total <= 0:
        raise HTTPException(status_code=422, detail="Recovery total must be greater than zero")

    receivable = (
        db.query(LoanReceivable)
        .filter(LoanReceivable.id == receivable_id, LoanReceivable.user_id == payload.user_id)
        .with_for_update().first()
    )
    if not receivable:
        raise HTTPException(status_code=404, detail="Loan receivable not found")
    if payload.principal_amount > receivable.outstanding_principal:
        raise HTTPException(status_code=422, detail="Principal recovery exceeds outstanding principal")
    account = _owned_account(db, payload.user_id, payload.account_id)

    try:
        tx = Transaction(
            user_id=payload.user_id, account_id=account.id, category_id=None,
            transaction_type="income", amount=total,
            description=payload.notes or f"Loan recovery: {receivable.borrower_name} - {receivable.name}",
            transaction_date=payload.transaction_date, reference=payload.reference,
        )
        db.add(tx)
        db.flush()
        movement = LoanMovement(
            user_id=payload.user_id, loan_id=None, receivable_id=receivable.id,
            transaction_id=tx.id, movement_type="recovery",
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount, fee_amount=payload.fee_amount,
        )
        db.add(movement)
        receivable.outstanding_principal -= payload.principal_amount
        receivable.status = "closed" if receivable.outstanding_principal == 0 else "active"
        account.balance = (account.balance or Decimal("0")) + total
        db.commit()
        db.refresh(movement)
        return {"status": "success", "transaction_id": tx.id, "movement": _movement_dict(movement), "loan_receivable": _receivable_dict(receivable), "account_balance": float(account.balance)}
    except Exception:
        db.rollback()
        raise


# ============================================================
# LIABILITIES
# ============================================================

@router.get("/api/liabilities")
def list_liabilities(user_id: int = Query(default=1, ge=1), db: Session = Depends(get_db)):
    items = db.query(Liability).filter(Liability.user_id == user_id).order_by(Liability.created_at.desc()).all()
    return {
        "status": "success", "liabilities": [_liability_dict(x) for x in items],
        "total_outstanding": float(sum((x.outstanding_amount for x in items if x.status == "active"), Decimal("0"))),
    }


@router.post("/api/liabilities")
def create_liability(payload: LiabilityPayload, db: Session = Depends(get_db)):
    _owned_user(db, payload.user_id)
    if payload.outstanding_amount > payload.original_amount:
        raise HTTPException(status_code=400, detail="Outstanding amount cannot exceed original amount")
    item = Liability(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "success", "liability": _liability_dict(item)}
