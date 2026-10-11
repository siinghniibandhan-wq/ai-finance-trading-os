# ============================================================
# FINANCIAL OS — SECURE ACCOUNTS API
# Every operation is restricted to the authenticated user.
# Existing database tables are preserved.
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
from app.routes.auth import get_current_user


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"],
)


# ============================================================
# CREATE ACCOUNT
# The authenticated user's ID determines account ownership.
# ============================================================

@router.post("/", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Reject attempts to create accounts for another user.
    if account_data.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create an account for another user.",
        )

    account = Account(
        user_id=current_user.id,
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
# Return accounts belonging only to the authenticated user.
# ============================================================

@router.get("/", response_model=list[AccountResponse])
def list_accounts(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Preserve compatibility with existing frontend requests.
    # A different user_id must never expose another user's data.
    if user_id is not None and user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's accounts.",
        )

    return (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .order_by(Account.id.desc())
        .all()
    )


# ============================================================
# GET ACCOUNT
# The account must belong to the authenticated user.
# ============================================================

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
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
# Prevent changes to accounts owned by another user.
# ============================================================

@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
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

    # Never allow an update to transfer account ownership.
    if (
        "user_id" in update_data
        and update_data["user_id"] != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot change account ownership.",
        )

    # Keep ownership fixed even if the update contains user_id.
    update_data.pop("user_id", None)

    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


# ============================================================
# DELETE ACCOUNT
# Delete only accounts owned by the authenticated user.
# ============================================================

@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
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
