from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Account
from database.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
)


router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"],
)


@router.get("/", response_model=list[AccountResponse])
def get_accounts(
    db: Session = Depends(get_db),
):
    return (
        db.query(Account)
        .filter(Account.is_active.is_(True))
        .order_by(Account.id.desc())
        .all()
    )


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return account


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=201,
)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
):
    account = Account(
        name=data.name,
        account_type=data.account_type,
        institution=data.institution,
        account_number=data.account_number,
        currency=data.currency,
        opening_balance=data.opening_balance,
        current_balance=data.opening_balance,
        notes=data.notes,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
)
def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


@router.delete("/{account_id}")
def archive_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    account.is_active = False

    db.commit()

    return {
        "message": "Account archived successfully",
        "account_id": account_id,
    }
