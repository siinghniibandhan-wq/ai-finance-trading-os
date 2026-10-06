# ============================================================
# TRANSACTIONS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User, Account, Category, Transaction
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
)


router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


# ============================================================
# CREATE TRANSACTION
# ============================================================

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Check user
    # --------------------------------------------------------
    user = (
        db.query(User)
        .filter(User.id == transaction_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # --------------------------------------------------------
    # Check account belongs to the same user
    # --------------------------------------------------------
    account = (
        db.query(Account)
        .filter(
            Account.id == transaction_data.account_id,
            Account.user_id == transaction_data.user_id,
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found for this user",
        )

    # --------------------------------------------------------
    # Check category belongs to the same user
    # --------------------------------------------------------
    if transaction_data.category_id is not None:

        category = (
            db.query(Category)
            .filter(
                Category.id == transaction_data.category_id,
                Category.user_id == transaction_data.user_id,
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found for this user",
            )

    # --------------------------------------------------------
    # Create transaction
    # --------------------------------------------------------
    transaction = Transaction(
        user_id=transaction_data.user_id,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        transaction_type=transaction_data.transaction_type,
        amount=transaction_data.amount,
        description=transaction_data.description,
        transaction_date=transaction_data.transaction_date,
        reference=transaction_data.reference,
    )

    db.add(transaction)

    # --------------------------------------------------------
    # UPDATE ACCOUNT BALANCE
    # --------------------------------------------------------
    if transaction_data.transaction_type in [
        "income",
        "refund",
        "interest",
        "dividend",
    ]:
        account.balance += transaction_data.amount

    elif transaction_data.transaction_type in [
        "expense",
        "withdrawal",
        "tax",
        "loan_repayment",
    ]:
        account.balance -= transaction_data.amount

    db.commit()
    db.refresh(transaction)

    return transaction


# ============================================================
# GET ALL TRANSACTIONS
# ============================================================

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    user_id: int,
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )

    return transactions


# ============================================================
# GET SINGLE TRANSACTION
# ============================================================

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return transaction


# ============================================================
# UPDATE TRANSACTION
# ============================================================

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    # --------------------------------------------------------
    # Validate new account if provided
    # --------------------------------------------------------
    if transaction_data.account_id is not None:

        account = (
            db.query(Account)
            .filter(
                Account.id == transaction_data.account_id,
                Account.user_id == transaction.user_id,
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not found for this user",
            )

    # --------------------------------------------------------
    # Validate new category if provided
    # --------------------------------------------------------
    if transaction_data.category_id is not None:

        category = (
            db.query(Category)
            .filter(
                Category.id == transaction_data.category_id,
                Category.user_id == transaction.user_id,
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found for this user",
            )

    # --------------------------------------------------------
    # Update only supplied fields
    # --------------------------------------------------------
    update_data = transaction_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)

    return transaction


# ============================================================
# DELETE TRANSACTION
# ============================================================

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }
