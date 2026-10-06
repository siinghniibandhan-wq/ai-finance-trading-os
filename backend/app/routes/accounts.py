# ============================================================
# FINANCIAL OS
# ACCOUNTS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, User
from app.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"],
)


# ============================================================
# CREATE ACCOUNT
# ============================================================

@router.post("/", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
):
    # Make sure the user exists.
    user = (
        db.query(User)
        .filter(User.id == account_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    account = Account(
        user_id=account_data.user_id,
        name=account_data.name,
        account_type=account_data.account_type,
        institution=account_data.institution,
        account_number=account_data.account_number,
        currency=account_data.currency,
        balance=account_data.balance,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


# ============================================================
# LIST ACCOUNTS
# ============================================================

@router.get("/", response_model=list[AccountResponse])
def list_accounts(
    user_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(Account)
        .filter(Account.user_id == user_id)
        .order_by(Account.id.desc())
        .all()
    )


# ============================================================
# GET ACCOUNT
# ============================================================

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    return account


# ============================================================
# UPDATE ACCOUNT
# ============================================================

@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    update_data = account_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


# ============================================================
# DELETE ACCOUNT
# ============================================================

@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    db.delete(account)
    db.commit()

    return {
        "status": "deleted",
        "account_id": account_id,
    }
