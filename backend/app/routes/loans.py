# ============================================================
# FINANCIAL OS
# LOANS & LIABILITIES API
#
# Purpose:
# 1. Create and list loans.
# 2. Automatically create one linked liability per loan.
# 3. Create and list other liabilities.
# 4. Validate user and account ownership.
# 5. Use database transactions and rollback on failure.
#
# IMPORTANT:
# This stage does not yet create financial transactions,
# change account balances, or process loan repayments.
# Those operations will be integrated in a later stage.
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, Liability, Loan, User


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Loans & Liabilities"]
)


# ============================================================
# LOAN REQUEST SCHEMA
# ============================================================

class LoanPayload(BaseModel):

    # User who owns this loan.
    user_id: int = Field(default=1, ge=1)

    # Basic loan information.
    name: str = Field(min_length=1, max_length=150)

    lender_name: str = Field(
        min_length=1,
        max_length=150,
    )

    loan_type: str = Field(
        min_length=1,
        max_length=60,
    )

    # Original contractual principal.
    principal_amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    # Amount actually disbursed by the lender.
    amount_disbursed: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    # Optional receiving bank account.
    deposit_account_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    # Interest information.
    interest_rate: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=7,
        decimal_places=4,
    )

    interest_type: str = "reducing_balance"

    # Repayment terms.
    tenure_months: Optional[int] = Field(
        default=None,
        gt=0,
        le=600,
    )

    emi_amount: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    start_date: date

    first_payment_date: Optional[date] = None

    repayment_frequency: str = "monthly"

    # Fees and references.
    processing_fee: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=18,
        decimal_places=2,
    )

    reference_number: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    notes: Optional[str] = None


# ============================================================
# LIABILITY REQUEST SCHEMA
#
# Used for liabilities that are not already represented by
# a Loan record.
# ============================================================

class LiabilityPayload(BaseModel):

    user_id: int = Field(default=1, ge=1)

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    liability_type: str = Field(
        default="other",
        max_length=60,
    )

    original_amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    outstanding_amount: Decimal = Field(
        ge=0,
        max_digits=18,
        decimal_places=2,
    )

    due_date: Optional[date] = None

    notes: Optional[str] = None


# ============================================================
# RESPONSE SERIALIZATION
#
# Convert database models into JSON-safe dictionaries.
# Monetary values are returned as strings to preserve decimal
# precision.
# ============================================================

def _loan_dict(loan: Loan):

    return {
        "id": loan.id,
        "user_id": loan.user_id,
        "name": loan.name,
        "lender_name": loan.lender_name,
        "loan_type": loan.loan_type,

        "principal_amount": str(
            loan.principal_amount
        ),

        "amount_disbursed": str(
            loan.amount_disbursed
        ),

        "outstanding_principal": str(
            loan.outstanding_principal
        ),

        "deposit_account_id": loan.deposit_account_id,

        "interest_rate": (
            str(loan.interest_rate)
            if loan.interest_rate is not None
            else None
        ),

        "interest_type": loan.interest_type,
        "tenure_months": loan.tenure_months,

        "emi_amount": (
            str(loan.emi_amount)
            if loan.emi_amount is not None
            else None
        ),

        "start_date": loan.start_date.isoformat(),

        "first_payment_date": (
            loan.first_payment_date.isoformat()
            if loan.first_payment_date
            else None
        ),

        "repayment_frequency": loan.repayment_frequency,

        "processing_fee": str(
            loan.processing_fee or Decimal("0")
        ),

        "reference_number": loan.reference_number,
        "notes": loan.notes,
        "status": loan.status,

        # One loan must correspond to one liability.
        "liability_id": (
            loan.liability.id
            if loan.liability
            else None
        ),
    }


def _liability_dict(liability: Liability):

    return {
        "id": liability.id,
        "user_id": liability.user_id,
        "name": liability.name,
        "liability_type": liability.liability_type,

        "original_amount": str(
            liability.original_amount
        ),

        "outstanding_amount": str(
            liability.outstanding_amount
        ),

        "loan_id": liability.loan_id,

        "due_date": (
            liability.due_date.isoformat()
            if liability.due_date
            else None
        ),

        "notes": liability.notes,
        "status": liability.status,
    }


# ============================================================
# GET ALL LOANS
#
# Example:
# GET /api/loans?user_id=1
# ============================================================

@router.get("/api/loans")
def list_loans(
    user_id: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
):

    loans = (
        db.query(Loan)
        .filter(Loan.user_id == user_id)
        .order_by(Loan.created_at.desc())
        .all()
    )

    return {
        "status": "success",
        "loans": [
            _loan_dict(loan)
            for loan in loans
        ],
    }


# ============================================================
# CREATE LOAN
#
# Creates:
# 1. One Loan record.
# 2. One linked Liability record.
#
# Both records are committed together.
#
# This endpoint does not yet change the bank account balance
# or create a transaction. Avoid performing those operations
# here until the transaction integration is implemented.
# ============================================================

@router.post("/api/loans")
def create_loan(
    payload: LoanPayload,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate the user.
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == payload.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    # --------------------------------------------------------
    # Validate the principal and disbursed amount.
    # --------------------------------------------------------

    if payload.amount_disbursed > payload.principal_amount:

        raise HTTPException(
            status_code=400,
            detail=(
                "Amount disbursed cannot exceed "
                "the original principal."
            ),
        )

    # --------------------------------------------------------
    # Validate repayment dates.
    # --------------------------------------------------------

    if (
        payload.first_payment_date is not None
        and payload.first_payment_date < payload.start_date
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "First payment date cannot be before "
                "the loan start date."
            ),
        )

    # --------------------------------------------------------
    # Validate receiving account ownership.
    #
    # The account must belong to the same user as the loan.
    # --------------------------------------------------------

    if payload.deposit_account_id is not None:

        account = (
            db.query(Account)
            .filter(
                Account.id == payload.deposit_account_id,
                Account.user_id == payload.user_id,
            )
            .first()
        )

        if not account:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Deposit account not found "
                    "for this user."
                ),
            )

    # --------------------------------------------------------
    # Create loan and linked liability atomically.
    # --------------------------------------------------------

    try:

        loan_data = payload.model_dump()

        loan = Loan(
            **loan_data,

            # Initial outstanding principal.
            outstanding_principal=payload.principal_amount,
        )

        db.add(loan)

        # Obtain the loan ID before creating its liability.
        db.flush()

        liability = Liability(
            user_id=payload.user_id,
            name=payload.name,
            liability_type=payload.loan_type,

            original_amount=payload.principal_amount,

            outstanding_amount=payload.principal_amount,

            loan_id=loan.id,
        )

        db.add(liability)

        # Commit both records together.
        db.commit()

        db.refresh(loan)
        db.refresh(liability)

        return {
            "status": "success",
            "message": (
                "Loan and linked liability created successfully."
            ),
            "loan": _loan_dict(loan),
            "liability": _liability_dict(liability),
        }

    except Exception:

        # Roll back both records if anything fails.
        db.rollback()

        raise


# ============================================================
# GET ALL LIABILITIES
#
# Example:
# GET /api/liabilities?user_id=1
#
# Loan-linked liabilities are returned here too.
# Do not add loan-linked liabilities to loan totals again.
# ============================================================

@router.get("/api/liabilities")
def list_liabilities(
    user_id: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
):

    liabilities = (
        db.query(Liability)
        .filter(Liability.user_id == user_id)
        .order_by(Liability.created_at.desc())
        .all()
    )

    # Consolidated outstanding debt:
    # Each Liability row is counted once.
    total_outstanding = sum(
        (
            liability.outstanding_amount
            for liability in liabilities
            if liability.status == "active"
        ),
        Decimal("0"),
    )

    return {
        "status": "success",

        "liabilities": [
            _liability_dict(liability)
            for liability in liabilities
        ],

        "total_outstanding": str(
            total_outstanding
        ),
    }


# ============================================================
# CREATE OTHER LIABILITY
#
# Examples:
# - Money owed to a person.
# - An outstanding bill.
# - Another obligation not represented by a Loan record.
#
# Do not use this endpoint to create a second liability for
# an existing loan. Loan creation creates its linked
# liability automatically.
# ============================================================

@router.post("/api/liabilities")
def create_liability(
    payload: LiabilityPayload,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate the user.
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == payload.user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    # --------------------------------------------------------
    # Validate the outstanding amount.
    # --------------------------------------------------------

    if payload.outstanding_amount > payload.original_amount:

        raise HTTPException(
            status_code=400,
            detail=(
                "Outstanding amount cannot exceed "
                "the original amount."
            ),
        )

    # --------------------------------------------------------
    # Create the independent liability.
    # --------------------------------------------------------

    try:

        liability = Liability(
            user_id=payload.user_id,
            name=payload.name,
            liability_type=payload.liability_type,
            original_amount=payload.original_amount,
            outstanding_amount=payload.outstanding_amount,
            due_date=payload.due_date,
            notes=payload.notes,
        )

        db.add(liability)

        db.commit()

        db.refresh(liability)

        return {
            "status": "success",
            "message": "Liability created successfully.",
            "liability": _liability_dict(liability),
        }

    except Exception:

        db.rollback()

        raise
