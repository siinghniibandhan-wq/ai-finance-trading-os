from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Account, Category, Transaction
from database.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.is_deleted.is_(False))
        .order_by(Transaction.transaction_date.desc())
        .all()
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.is_deleted.is_(False),
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return transaction


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=201,
)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(
            Account.id == data.account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    if data.category_id is not None:
        category = (
            db.query(Category)
            .filter(
                Category.id == data.category_id,
                Category.is_active.is_(True),
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

    transaction = Transaction(
        account_id=data.account_id,
        category_id=data.category_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        merchant=data.merchant,
        reference_number=data.reference_number,
        transaction_date=data.transaction_date,
        notes=data.notes,
    )

    db.add(transaction)

    # Update account balance
    if data.transaction_type in [
        "income",
        "refund",
        "interest",
        "dividend",
    ]:
        account.current_balance += data.amount

    elif data.transaction_type in [
        "expense",
        "withdrawal",
        "tax",
        "loan_repayment",
    ]:
        account.current_balance -= data.amount

    db.commit()
    db.refresh(transaction)

    return transaction


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.is_deleted.is_(False),
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "account_id" in update_data:
        account = (
            db.query(Account)
            .filter(
                Account.id == update_data["account_id"],
                Account.is_active.is_(True),
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not found",
            )

    if "category_id" in update_data:
        category_id = update_data["category_id"]

        if category_id is not None:
            category = (
                db.query(Category)
                .filter(
                    Category.id == category_id,
                    Category.is_active.is_(True),
                )
                .first()
            )

            if not category:
                raise HTTPException(
                    status_code=404,
                    detail="Category not found",
                )

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.is_deleted.is_(False),
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    transaction.is_deleted = True

    db.commit()

    return {
        "message": "Transaction deleted successfully",
        "transaction_id": transaction_id,
  }
