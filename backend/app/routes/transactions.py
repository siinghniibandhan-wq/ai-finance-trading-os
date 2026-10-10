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
# ACCOUNT BALANCE EFFECT
# Keep the sign rules in one place so create, edit, and delete
# apply exactly opposite effects when a transaction is reversed.
# ============================================================

INCREASE_BALANCE_TYPES = {"income", "refund", "interest", "dividend"}
DECREASE_BALANCE_TYPES = {"expense", "withdrawal", "tax", "loan_repayment"}


def _apply_balance_effect(account: Account, transaction_type: str, amount):
    """Apply one transaction's balance effect to an account."""
    if transaction_type in INCREASE_BALANCE_TYPES:
        account.balance = (account.balance or 0) + amount
    elif transaction_type in DECREASE_BALANCE_TYPES:
        account.balance = (account.balance or 0) - amount


def _reverse_balance_effect(account: Account, transaction_type: str, amount):
    """Undo a previously applied transaction balance effect."""
    if transaction_type in INCREASE_BALANCE_TYPES:
        account.balance = (account.balance or 0) - amount
    elif transaction_type in DECREASE_BALANCE_TYPES:
        account.balance = (account.balance or 0) + amount


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

    if transaction_data.amount <= 0:
        raise HTTPException(status_code=422, detail="Transaction amount must be greater than zero")

    db.add(transaction)
    try:
        # Keep the transaction row and balance change in one DB transaction.
        _apply_balance_effect(account, transaction_data.transaction_type, transaction_data.amount)
        db.commit()
        db.refresh(transaction)
    except Exception:
        db.rollback()
        raise

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
        .with_for_update()
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = transaction_data.model_dump(exclude_unset=True)
    new_account_id = update_data.get("account_id", transaction.account_id)
    new_category_id = update_data.get("category_id", transaction.category_id)
    new_type = update_data.get("transaction_type", transaction.transaction_type)
    new_amount = update_data.get("amount", transaction.amount)

    if new_account_id is None:
        raise HTTPException(status_code=422, detail="An account is required")
    if new_type is None:
        raise HTTPException(status_code=422, detail="A transaction type is required")
    if new_amount is None or new_amount <= 0:
        raise HTTPException(status_code=422, detail="Transaction amount must be greater than zero")

    # Validate the destination account and category against this transaction's user.
    accounts_to_lock = sorted({transaction.account_id, new_account_id})
    accounts = (
        db.query(Account)
        .filter(Account.id.in_(accounts_to_lock), Account.user_id == transaction.user_id)
        .order_by(Account.id)
        .with_for_update()
        .all()
    )
    account_by_id = {account.id: account for account in accounts}
    old_account = account_by_id.get(transaction.account_id)
    new_account = account_by_id.get(new_account_id)

    if old_account is None:
        raise HTTPException(status_code=404, detail="Original account not found for this user")
    if new_account is None:
        raise HTTPException(status_code=404, detail="Account not found for this user")

    if new_category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == new_category_id, Category.user_id == transaction.user_id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found for this user")

    # Snapshot the old values before mutating the transaction.
    old_type = transaction.transaction_type
    old_amount = transaction.amount

    try:
        # Reverse the old transaction first, then apply the new transaction.
        _reverse_balance_effect(old_account, old_type, old_amount)

        for field, value in update_data.items():
            setattr(transaction, field, value)

        _apply_balance_effect(new_account, new_type, new_amount)
        db.commit()
        db.refresh(transaction)
    except Exception:
        db.rollback()
        raise

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
        .with_for_update()
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    account = (
        db.query(Account)
        .filter(Account.id == transaction.account_id, Account.user_id == transaction.user_id)
        .with_for_update()
        .first()
    )

    try:
        if account:
            _reverse_balance_effect(account, transaction.transaction_type, transaction.amount)
        db.delete(transaction)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Transaction deleted successfully"}
