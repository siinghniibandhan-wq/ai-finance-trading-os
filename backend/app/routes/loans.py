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
from app.finance_diary import record_finance_event
from app.routes.auth import get_current_user
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
    linked_account_id: Optional[int] = None
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
        "linked_account_id": x.linked_account_id,
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
def list_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(Loan).filter(Loan.user_id == current_user.id).order_by(Loan.created_at.desc()).all()
    return {"status": "success", "loans": [_loan_dict(x) for x in items]}


@router.post("/api/loans")
def create_loan(payload: LoanPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_user(db, current_user.id)
    if payload.amount_disbursed > payload.principal_amount:
        raise HTTPException(status_code=400, detail="Amount disbursed cannot exceed principal amount")
    if payload.deposit_account_id is not None:
        _owned_account(db, current_user.id, payload.deposit_account_id, lock=False)
    linked_account = None
    if payload.linked_account_id is not None:
        linked_account = _owned_account(db, current_user.id, payload.linked_account_id, lock=False)
        if (linked_account.account_type or "").strip().lower() != "loan":
            raise HTTPException(status_code=422, detail="Linked account must be a Loan Account.")
        existing_loan = db.query(Loan).filter(Loan.user_id == current_user.id, Loan.linked_account_id == linked_account.id).first()
        if existing_loan:
            raise HTTPException(status_code=409, detail="This account is already linked to a loan.")
    try:
        loan = Loan(**payload.model_dump(exclude={'user_id'}), user_id=current_user.id, outstanding_principal=payload.principal_amount)
        db.add(loan)
        db.flush()
        if linked_account is not None:
            linked_account.balance = payload.principal_amount
        liability = Liability(
            user_id=current_user.id, name=payload.name,
            liability_type=payload.loan_type,
            original_amount=payload.principal_amount,
            outstanding_amount=payload.principal_amount, loan_id=loan.id,
        )
        db.add(liability)
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_created",
            entity_type="loan", entity_id=loan.id,
            description=f"Created loan: {loan.name}",
            snapshot={
                "loan_id": loan.id, "liability_id": liability.id,
                "principal_amount": payload.principal_amount,
                "amount_disbursed": payload.amount_disbursed,
                "deposit_account_id": payload.deposit_account_id,
                "linked_account_id": payload.linked_account_id,
                "start_date": payload.start_date, "status": loan.status,
            },
        )
        db.commit()
        db.refresh(loan)
        return {"status": "success", "loan": _loan_dict(loan)}
    except Exception:
        db.rollback()
        raise


@router.post("/api/loans/{loan_id}/repayments")
def repay_loan(loan_id: int, payload: LoanMovementCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Record one cash repayment, splitting principal, interest and fees."""
    _owned_user(db, current_user.id)
    total = payload.principal_amount + payload.interest_amount + payload.fee_amount
    if total <= 0:
        raise HTTPException(status_code=422, detail="Repayment total must be greater than zero")

    loan = (
        db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == current_user.id)
        .with_for_update().first()
    )
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if payload.principal_amount > loan.outstanding_principal:
        raise HTTPException(status_code=422, detail="Principal repayment exceeds outstanding principal")
    account = _owned_account(db, current_user.id, payload.account_id)
    liability = db.query(Liability).filter(Liability.loan_id == loan.id, Liability.user_id == current_user.id).with_for_update().first()

    try:
        tx = Transaction(
            user_id=current_user.id, account_id=account.id, category_id=None,
            transaction_type="loan_repayment", amount=total,
            description=payload.notes or f"Loan repayment: {loan.name}",
            transaction_date=payload.transaction_date, reference=payload.reference,
        )
        db.add(tx)
        db.flush()
        movement = LoanMovement(
            user_id=current_user.id, loan_id=loan.id, receivable_id=None,
            transaction_id=tx.id, movement_type="repayment",
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount, fee_amount=payload.fee_amount,
        )
        db.add(movement)
        loan.outstanding_principal -= payload.principal_amount
        loan.status = "closed" if loan.outstanding_principal == 0 else "active"
        if loan.linked_account_id is not None:
            linked_account = _owned_account(db, current_user.id, loan.linked_account_id)
            linked_account.balance = loan.outstanding_principal
        if liability:
            liability.outstanding_amount = loan.outstanding_principal
            liability.status = "closed" if liability.outstanding_amount == 0 else "active"
        account.balance = (account.balance or Decimal("0")) - total
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_repayment_recorded",
            entity_type="loan_movement", entity_id=movement.id,
            description=f"Recorded repayment for loan: {loan.name}",
            snapshot={"loan_id": loan.id, "transaction_id": tx.id, "account_id": account.id,
                      "principal_amount": payload.principal_amount, "interest_amount": payload.interest_amount,
                      "fee_amount": payload.fee_amount, "total_amount": total,
                      "transaction_date": payload.transaction_date},
        )
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
def list_loan_receivables(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(LoanReceivable).filter(LoanReceivable.user_id == current_user.id).order_by(LoanReceivable.created_at.desc()).all()
    return {"status": "success", "loan_receivables": [_receivable_dict(x) for x in items]}


@router.post("/api/loan-receivables")
def create_loan_receivable(payload: LoanReceivableCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Disburse a loan to a borrower: cash decreases, receivable asset increases."""
    _owned_user(db, current_user.id)
    account = _owned_account(db, current_user.id, payload.source_account_id)
    if account.balance is not None and account.balance < payload.principal_amount:
        raise HTTPException(status_code=422, detail="Insufficient account balance for this loan disbursement")

    try:
        tx = Transaction(
            user_id=current_user.id, account_id=account.id, category_id=None,
            transaction_type="withdrawal", amount=payload.principal_amount,
            description=f"Loan given to {payload.borrower_name}: {payload.name}",
            transaction_date=payload.start_date, reference=payload.reference_number,
        )
        db.add(tx)
        db.flush()
        receivable = LoanReceivable(
            user_id=current_user.id, borrower_name=payload.borrower_name,
            name=payload.name, original_principal=payload.principal_amount,
            outstanding_principal=payload.principal_amount, source_account_id=account.id,
            disbursement_transaction_id=tx.id, interest_rate=payload.interest_rate,
            start_date=payload.start_date, due_date=payload.due_date,
            reference_number=payload.reference_number, notes=payload.notes, status="active",
        )
        db.add(receivable)
        db.flush()
        movement = LoanMovement(
            user_id=current_user.id, loan_id=None, receivable_id=receivable.id,
            transaction_id=tx.id, movement_type="disbursement",
            principal_amount=payload.principal_amount,
            interest_amount=Decimal("0"), fee_amount=Decimal("0"),
        )
        db.add(movement)
        account.balance = (account.balance or Decimal("0")) - payload.principal_amount
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_disbursement_recorded",
            entity_type="loan_receivable", entity_id=receivable.id,
            description=f"Disbursed loan to {receivable.borrower_name}: {receivable.name}",
            snapshot={"transaction_id": tx.id, "account_id": account.id,
                      "principal_amount": payload.principal_amount, "start_date": payload.start_date},
        )
        db.commit()
        db.refresh(receivable)
        return {"status": "success", "loan_receivable": _receivable_dict(receivable), "transaction_id": tx.id, "account_balance": float(account.balance)}
    except Exception:
        db.rollback()
        raise


@router.post("/api/loan-receivables/{receivable_id}/recoveries")
def recover_loan(receivable_id: int, payload: LoanMovementCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Record cash received from a borrower; principal is not income."""
    _owned_user(db, current_user.id)
    total = payload.principal_amount + payload.interest_amount + payload.fee_amount
    if total <= 0:
        raise HTTPException(status_code=422, detail="Recovery total must be greater than zero")

    receivable = (
        db.query(LoanReceivable)
        .filter(LoanReceivable.id == receivable_id, LoanReceivable.user_id == current_user.id)
        .with_for_update().first()
    )
    if not receivable:
        raise HTTPException(status_code=404, detail="Loan receivable not found")
    if payload.principal_amount > receivable.outstanding_principal:
        raise HTTPException(status_code=422, detail="Principal recovery exceeds outstanding principal")
    account = _owned_account(db, current_user.id, payload.account_id)

    try:
        tx = Transaction(
            user_id=current_user.id, account_id=account.id, category_id=None,
            transaction_type="income", amount=total,
            description=payload.notes or f"Loan recovery: {receivable.borrower_name} - {receivable.name}",
            transaction_date=payload.transaction_date, reference=payload.reference,
        )
        db.add(tx)
        db.flush()
        movement = LoanMovement(
            user_id=current_user.id, loan_id=None, receivable_id=receivable.id,
            transaction_id=tx.id, movement_type="recovery",
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount, fee_amount=payload.fee_amount,
        )
        db.add(movement)
        receivable.outstanding_principal -= payload.principal_amount
        receivable.status = "closed" if receivable.outstanding_principal == 0 else "active"
        account.balance = (account.balance or Decimal("0")) + total
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_recovery_recorded",
            entity_type="loan_movement", entity_id=movement.id,
            description=f"Recorded recovery for loan receivable: {receivable.name}",
            snapshot={"receivable_id": receivable.id, "transaction_id": tx.id, "account_id": account.id,
                      "principal_amount": payload.principal_amount, "interest_amount": payload.interest_amount,
                      "fee_amount": payload.fee_amount, "total_amount": total,
                      "transaction_date": payload.transaction_date},
        )
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
def list_liabilities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(Liability).filter(Liability.user_id == current_user.id).order_by(Liability.created_at.desc()).all()
    active_liabilities = [x for x in items if x.status == "active"]
    total = sum((x.outstanding_amount for x in active_liabilities), Decimal("0"))
    liability_rows = [_liability_dict(x) for x in items]

    # Credit products store the actual amount owed in Account.balance. Their
    # credit_limit is a facility limit, never a liability balance.
    # Loan accounts linked to a Loan are already represented by that loan's
    # Liability row, so only unlinked loan accounts are added below.
    account_liability_types = {
        "credit_card", "creditcard", "credit_card_account",
        "credit_line", "creditline", "credit_line_account",
        "cash_credit", "cash_credit_account", "overdraft", "od",
        "loan", "loan_account", "personal_loan", "home_loan", "term_loan",
    }
    accounts = (
        db.query(Account)
        .filter(Account.user_id == current_user.id, Account.is_active.is_(True))
        .order_by(Account.id.desc())
        .all()
    )
    linked_loan_account_ids = {
        loan.linked_account_id
        for loan in db.query(Loan).filter(Loan.user_id == current_user.id, Loan.linked_account_id.isnot(None)).all()
    }
    represented_loan_account_ids = {
        loan.linked_account_id
        for loan in db.query(Loan).join(Liability, Liability.loan_id == Loan.id)
        .filter(Loan.user_id == current_user.id, Liability.user_id == current_user.id, Liability.status == "active", Loan.linked_account_id.isnot(None))
        .all()
    }
    liability_loan_ids = {item.loan_id for item in items if item.loan_id is not None}
    # Legacy/imported loan contracts may exist without a matching Liability row.
    # Include their outstanding principal once, while linked account balances
    # remain excluded below.
    unrepresented_loans = (
        db.query(Loan)
        .filter(Loan.user_id == current_user.id, Loan.status == "active")
        .all()
    )
    for loan in unrepresented_loans:
        if loan.id in liability_loan_ids:
            continue
        outstanding = max(Decimal(str(loan.outstanding_principal or 0)), Decimal("0"))
        if outstanding <= 0:
            continue
        total += outstanding
        liability_rows.append({
            "id": f"loan-{loan.id}",
            "user_id": loan.user_id,
            "name": loan.name,
            "liability_type": loan.loan_type,
            "original_amount": float(loan.principal_amount),
            "outstanding_amount": float(outstanding),
            "loan_id": loan.id,
            "due_date": None,
            "notes": "Outstanding principal from loan contract.",
            "status": "active",
            "account_id": loan.linked_account_id,
        })
    for account in accounts:
        account_type = (account.account_type or "").strip().lower().replace("-", "_").replace(" ", "_")
        if account_type not in account_liability_types:
            continue
        if account_type in {"loan", "loan_account"} and account.id in represented_loan_account_ids:
            continue
        # A linked loan without an active Liability is still represented by
        # its Loan contract; avoid counting its account balance twice.
        if account_type in {"loan", "loan_account"} and account.id in linked_loan_account_ids:
            continue
        outstanding = max(Decimal(str(account.balance or 0)), Decimal("0"))
        if outstanding <= 0:
            continue
        total += outstanding
        liability_rows.append({
            "id": f"account-{account.id}",
            "user_id": account.user_id,
            "name": account.name,
            "liability_type": account_type,
            "original_amount": float(outstanding),
            "outstanding_amount": float(outstanding),
            "loan_id": None,
            "due_date": None,
            "notes": "Outstanding balance from linked financial account.",
            "status": "active",
            "account_id": account.id,
        })

    return {
        "status": "success", "liabilities": liability_rows,
        "total_outstanding": float(total),
    }


@router.post("/api/liabilities")
def create_liability(payload: LiabilityPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_user(db, current_user.id)
    if payload.outstanding_amount > payload.original_amount:
        raise HTTPException(status_code=400, detail="Outstanding amount cannot exceed original amount")
    item = Liability(**payload.model_dump(exclude={'user_id'}), user_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "success", "liability": _liability_dict(item)}


# ============================================================
# SAFE CORRECTION / CANCELLATION OF LINKED LOAN MOVEMENTS
# Use these endpoints instead of editing/deleting their ordinary
# transactions. All linked balances are changed in one DB commit.
# ============================================================

class LoanMovementCorrection(BaseModel):
    user_id: int = 1
    account_id: int
    principal_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    interest_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    fee_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    transaction_date: date
    reference: Optional[str] = None
    notes: Optional[str] = None


@router.put("/api/loan-movements/{movement_id}")
def correct_loan_movement(movement_id: int, payload: LoanMovementCorrection, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Correct repayment/recovery values without duplicating its transaction."""
    _owned_user(db, current_user.id)
    movement = (
        db.query(LoanMovement)
        .filter(LoanMovement.id == movement_id, LoanMovement.user_id == current_user.id)
        .with_for_update().first()
    )
    if not movement:
        raise HTTPException(status_code=404, detail="Loan movement not found")
    if movement.movement_type not in {"repayment", "recovery"}:
        raise HTTPException(status_code=409, detail="Only repayment and recovery movements can be corrected here")

    tx = db.query(Transaction).filter(Transaction.id == movement.transaction_id, Transaction.user_id == current_user.id).with_for_update().first()
    if not tx:
        raise HTTPException(status_code=409, detail="Linked transaction is missing; correction stopped")
    account = _owned_account(db, current_user.id, tx.account_id)
    if payload.account_id != tx.account_id:
        # Account switching is intentionally disallowed until both accounts can be
        # locked and ownership verified in a dedicated transfer-safe workflow.
        raise HTTPException(status_code=422, detail="Changing the account is not supported; cancel and re-record on the correct account")

    old_total = Decimal(tx.amount)
    new_total = payload.principal_amount + payload.interest_amount + payload.fee_amount
    try:
        if movement.movement_type == "repayment":
            loan = db.query(Loan).filter(Loan.id == movement.loan_id, Loan.user_id == current_user.id).with_for_update().first()
            if not loan:
                raise HTTPException(status_code=409, detail="Linked loan is missing")
            available_principal = Decimal(loan.outstanding_principal) + Decimal(movement.principal_amount)
            if payload.principal_amount > available_principal:
                raise HTTPException(status_code=422, detail="Corrected principal exceeds available outstanding principal")
            loan.outstanding_principal = available_principal - payload.principal_amount
            loan.status = "closed" if loan.outstanding_principal == 0 else "active"
            liability = db.query(Liability).filter(Liability.loan_id == loan.id, Liability.user_id == current_user.id).with_for_update().first()
            if liability:
                liability.outstanding_amount = loan.outstanding_principal
                liability.status = "closed" if liability.outstanding_amount == 0 else "active"
            # Repayment reduces cash; undo old reduction and apply new reduction.
            account.balance = (account.balance or Decimal("0")) + old_total - new_total
            tx.transaction_type = "loan_repayment"
        else:
            receivable = db.query(LoanReceivable).filter(LoanReceivable.id == movement.receivable_id, LoanReceivable.user_id == current_user.id).with_for_update().first()
            if not receivable:
                raise HTTPException(status_code=409, detail="Linked loan receivable is missing")
            available_principal = Decimal(receivable.outstanding_principal) + Decimal(movement.principal_amount)
            if payload.principal_amount > available_principal:
                raise HTTPException(status_code=422, detail="Corrected principal exceeds available outstanding principal")
            receivable.outstanding_principal = available_principal - payload.principal_amount
            receivable.status = "closed" if receivable.outstanding_principal == 0 else "active"
            # Recovery increases cash; replace old amount with corrected amount.
            account.balance = (account.balance or Decimal("0")) - old_total + new_total
            tx.transaction_type = "income"

        movement.principal_amount = payload.principal_amount
        movement.interest_amount = payload.interest_amount
        movement.fee_amount = payload.fee_amount
        tx.amount = new_total
        tx.transaction_date = payload.transaction_date
        tx.reference = payload.reference
        if payload.notes is not None:
            tx.description = payload.notes
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_movement_corrected",
            entity_type="loan_movement", entity_id=movement.id,
            description=f"Corrected {movement.movement_type} for loan movement {movement.id}",
            snapshot={"transaction_id": tx.id, "account_id": account.id,
                      "principal_amount": movement.principal_amount, "interest_amount": movement.interest_amount,
                      "fee_amount": movement.fee_amount, "transaction_amount": tx.amount,
                      "transaction_date": tx.transaction_date},
        )
        db.commit()
        db.refresh(movement)
        return {"status": "success", "movement": _movement_dict(movement), "transaction_id": tx.id, "account_balance": float(account.balance)}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.delete("/api/loan-movements/{movement_id}")
def cancel_loan_movement(
    movement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a repayment/recovery and reverse all linked balances atomically."""
    _owned_user(db, current_user.id)
    movement = db.query(LoanMovement).filter(LoanMovement.id == movement_id, LoanMovement.user_id == current_user.id).with_for_update().first()
    if not movement:
        raise HTTPException(status_code=404, detail="Loan movement not found")
    if movement.movement_type not in {"repayment", "recovery"}:
        raise HTTPException(status_code=409, detail="Disbursement cancellation requires the dedicated loan cancellation workflow")
    tx = db.query(Transaction).filter(Transaction.id == movement.transaction_id, Transaction.user_id == current_user.id).with_for_update().first()
    if not tx:
        raise HTTPException(status_code=409, detail="Linked transaction is missing; cancellation stopped")
    account = _owned_account(db, current_user.id, tx.account_id)
    principal = Decimal(movement.principal_amount)
    total = Decimal(tx.amount)
    try:
        if movement.movement_type == "repayment":
            loan = db.query(Loan).filter(Loan.id == movement.loan_id, Loan.user_id == current_user.id).with_for_update().first()
            if not loan:
                raise HTTPException(status_code=409, detail="Linked loan is missing")
            loan.outstanding_principal = Decimal(loan.outstanding_principal) + principal
            loan.status = "active"
            liability = db.query(Liability).filter(Liability.loan_id == loan.id, Liability.user_id == current_user.id).with_for_update().first()
            if liability:
                liability.outstanding_amount = loan.outstanding_principal
                liability.status = "active"
            account.balance = (account.balance or Decimal("0")) + total
        else:
            receivable = db.query(LoanReceivable).filter(LoanReceivable.id == movement.receivable_id, LoanReceivable.user_id == current_user.id).with_for_update().first()
            if not receivable:
                raise HTTPException(status_code=409, detail="Linked loan receivable is missing")
            receivable.outstanding_principal = Decimal(receivable.outstanding_principal) + principal
            receivable.status = "active"
            account.balance = (account.balance or Decimal("0")) - total

        # Delete the linked movement first, then its transaction (FK is RESTRICT).
        db.delete(movement)
        db.flush()
        db.delete(tx)
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_movement_cancelled",
            entity_type="loan_movement", entity_id=movement_id,
            description=f"Cancelled {movement.movement_type} for loan movement {movement_id}",
            snapshot={"transaction_id": tx.id, "movement_type": movement.movement_type,
                      "loan_id": movement.loan_id, "receivable_id": movement.receivable_id,
                      "principal_amount": movement.principal_amount, "interest_amount": movement.interest_amount,
                      "fee_amount": movement.fee_amount, "reversed_amount": tx.amount,
                      "account_id": account.id},
        )
        db.commit()
        return {"status": "success", "message": "Loan movement cancelled and linked balances reversed", "movement_id": movement_id, "account_balance": float(account.balance)}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# ============================================================
# SAFE DISBURSEMENT CANCELLATION
# Cancel only the original disbursement, and only when no later
# repayments/recoveries exist. All reversals happen in one commit.
# ============================================================

@router.delete("/api/loans/{loan_id}/disbursement")
def cancel_borrowed_loan_disbursement(
    loan_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Cancel a borrowed-loan disbursement before any repayment was recorded."""
    _owned_user(db, current_user.id)
    loan = (
        db.query(Loan)
        .filter(Loan.id == loan_id, Loan.user_id == current_user.id)
        .with_for_update()
        .first()
    )
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if not loan.disbursement_transaction_id:
        raise HTTPException(
            status_code=409,
            detail="This loan has no linked disbursement transaction and cannot be safely cancelled here.",
        )

    # A loan can only be cancelled at its origin if no repayments exist.
    movements = (
        db.query(LoanMovement.id)
        .filter(LoanMovement.loan_id == loan.id, LoanMovement.user_id == current_user.id)
        .first()
    )
    if movements:
        raise HTTPException(
            status_code=409,
            detail="This loan has recorded movements. Cancel its repayments first before cancelling the disbursement.",
        )

    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id == loan.disbursement_transaction_id,
            Transaction.user_id == current_user.id,
        )
        .with_for_update()
        .first()
    )
    if not tx:
        raise HTTPException(status_code=409, detail="Linked disbursement transaction is missing")
    if (tx.transaction_type or "").lower() != "income":
        raise HTTPException(
            status_code=409,
            detail="Linked disbursement is not an income transaction; automatic reversal was stopped.",
        )

    account = _owned_account(db, current_user.id, tx.account_id)
    try:
        # Reverse the original cash-in before deleting linked records.
        account.balance = (account.balance or Decimal("0")) - Decimal(tx.amount)
        liability = db.query(Liability).filter(Liability.loan_id == loan.id, Liability.user_id == current_user.id).with_for_update().first()
        if liability:
            db.delete(liability)
            db.flush()
        db.delete(loan)
        db.flush()
        db.delete(tx)
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_disbursement_cancelled",
            entity_type="loan", entity_id=loan_id,
            description=f"Cancelled borrowed-loan disbursement for loan {loan_id}",
            snapshot={"transaction_id": tx.id, "account_id": account.id, "reversed_amount": tx.amount,
                      "loan_name": loan.name, "principal_amount": loan.principal_amount},
        )
        db.commit()
        return {
            "status": "success",
            "message": "Borrowed-loan disbursement cancelled and account balance reversed",
            "loan_id": loan_id,
            "transaction_id": tx.id,
            "account_balance": float(account.balance),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.delete("/api/loan-receivables/{receivable_id}/disbursement")
def cancel_loan_given_disbursement(
    receivable_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Cancel a loan given to another person before any recovery exists."""
    _owned_user(db, current_user.id)
    receivable = (
        db.query(LoanReceivable)
        .filter(LoanReceivable.id == receivable_id, LoanReceivable.user_id == current_user.id)
        .with_for_update()
        .first()
    )
    if not receivable:
        raise HTTPException(status_code=404, detail="Loan receivable not found")
    if not receivable.disbursement_transaction_id:
        raise HTTPException(
            status_code=409,
            detail="This receivable has no linked disbursement transaction and cannot be safely cancelled here.",
        )

    movement_rows = (
        db.query(LoanMovement)
        .filter(LoanMovement.receivable_id == receivable.id, LoanMovement.user_id == current_user.id)
        .with_for_update()
        .all()
    )
    if any(m.movement_type == "recovery" for m in movement_rows):
        raise HTTPException(
            status_code=409,
            detail="This receivable has recorded recoveries. Cancel its recoveries first before cancelling the disbursement.",
        )
    disbursement_movements = [m for m in movement_rows if m.movement_type == "disbursement"]
    if len(disbursement_movements) != 1:
        raise HTTPException(
            status_code=409,
            detail="Expected exactly one linked disbursement movement; automatic cancellation was stopped.",
        )

    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id == receivable.disbursement_transaction_id,
            Transaction.user_id == current_user.id,
        )
        .with_for_update()
        .first()
    )
    if not tx:
        raise HTTPException(status_code=409, detail="Linked disbursement transaction is missing")
    if (tx.transaction_type or "").lower() != "withdrawal":
        raise HTTPException(
            status_code=409,
            detail="Linked disbursement is not a withdrawal; automatic reversal was stopped.",
        )

    account = _owned_account(db, current_user.id, tx.account_id)
    try:
        # Reverse the original cash-out and remove its linked movement first
        # because LoanMovement.transaction_id uses ON DELETE RESTRICT.
        account.balance = (account.balance or Decimal("0")) + Decimal(tx.amount)
        db.delete(disbursement_movements[0])
        db.flush()
        db.delete(receivable)
        db.flush()
        db.delete(tx)
        record_finance_event(
            db, user_id=current_user.id, event_type="loan_given_disbursement_cancelled",
            entity_type="loan_receivable", entity_id=receivable_id,
            description=f"Cancelled loan-given disbursement for receivable {receivable_id}",
            snapshot={"transaction_id": tx.id, "account_id": account.id, "reversed_amount": tx.amount,
                      "borrower_name": receivable.borrower_name, "principal_amount": receivable.original_principal},
        )
        db.commit()
        return {
            "status": "success",
            "message": "Loan-given disbursement cancelled and account balance restored",
            "receivable_id": receivable_id,
            "transaction_id": tx.id,
            "account_balance": float(account.balance),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
