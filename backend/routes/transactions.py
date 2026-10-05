from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Account, Category, Transaction
from database.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


# =====================================================
# TRANSACTIONS ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


# =====================================================
# BALANCE EFFECT HELPER
#
# Positive effect = money enters account
# Negative effect = money leaves account
#
# IMPORTANT:
# Keep this function as the single place where
# transaction balance behavior is defined.
# =====================================================

def get_balance_effect(transaction_type, amount):
    """
    Return how much this transaction changes
    the account balance.
    """

    if transaction_type in [
        "income",
        "refund",
        "interest",
        "dividend",
    ]:
        return amount

    if transaction_type in [
        "expense",
        "withdrawal",
        "tax",
        "loan_repayment",
    ]:
        return -amount

    # Transfer/investment/other transaction types
    # currently do not change the account balance here.
    #
    # They can be given dedicated accounting logic later
    # when the corresponding transaction structure is added.
    return 0


# =====================================================
# GET ALL TRANSACTIONS
# =====================================================

@router.get(
    "/",
    response_model=list[TransactionResponse],
)
def get_transactions(
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(
            Transaction.is_deleted.is_(False)
        )
        .order_by(
            Transaction.transaction_date.desc()
        )
        .all()
    )


# =====================================================
# GET SINGLE TRANSACTION
# =====================================================

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


# =====================================================
# CREATE TRANSACTION
# =====================================================

@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=201,
)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):

    # =================================================
    # VALIDATE ACCOUNT
    # =================================================

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

    # =================================================
    # VALIDATE CATEGORY
    # =================================================

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

    # =================================================
    # CREATE TRANSACTION
    # =================================================

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

    # =================================================
    # UPDATE ACCOUNT BALANCE
    # =================================================

    balance_effect = get_balance_effect(
        data.transaction_type,
        data.amount,
    )

    account.current_balance += balance_effect

    # =================================================
    # SAVE
    # =================================================

    db.commit()
    db.refresh(transaction)

    return transaction


# =====================================================
# UPDATE TRANSACTION
#
# IMPORTANT:
# 1. Reverse old transaction effect.
# 2. Apply new transaction effect.
#
# This prevents incorrect balances when the user edits
# amount, type or account.
# =====================================================

@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):

    # =================================================
    # FIND EXISTING TRANSACTION
    # =================================================

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

    # =================================================
    # SAVE OLD VALUES BEFORE CHANGES
    # =================================================

    old_account_id = transaction.account_id
    old_transaction_type = transaction.transaction_type
    old_amount = transaction.amount

    # =================================================
    # FIND OLD ACCOUNT
    # =================================================

    old_account = (
        db.query(Account)
        .filter(
            Account.id == old_account_id,
        )
        .first()
    )

    if not old_account:
        raise HTTPException(
            status_code=404,
            detail="Original account not found",
        )

    # =================================================
    # VALIDATE NEW ACCOUNT
    # =================================================

    new_account_id = data.account_id

    if new_account_id is None:
        new_account_id = old_account_id

    new_account = (
        db.query(Account)
        .filter(
            Account.id == new_account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not new_account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    # =================================================
    # VALIDATE CATEGORY
    # =================================================

    update_data = data.model_dump(
        exclude_unset=True
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

    # =================================================
    # CALCULATE OLD BALANCE EFFECT
    # =================================================

    old_balance_effect = get_balance_effect(
        old_transaction_type,
        old_amount,
    )

    # =================================================
    # REVERSE OLD TRANSACTION
    #
    # Example:
    # Old expense = -500
    # Reverse = +500
    # =================================================

    old_account.current_balance -= old_balance_effect

    # =================================================
    # APPLY NEW TRANSACTION FIELDS
    # =================================================

    for field, value in update_data.items():
        setattr(
            transaction,
            field,
            value,
        )

    # =================================================
    # CALCULATE NEW BALANCE EFFECT
    # =================================================

    new_transaction_type = transaction.transaction_type
    new_amount = transaction.amount

    new_balance_effect = get_balance_effect(
        new_transaction_type,
        new_amount,
    )

    # =================================================
    # APPLY NEW TRANSACTION EFFECT
    # =================================================

    new_account.current_balance += new_balance_effect

    # =================================================
    # SAVE
    # =================================================

    db.commit()
    db.refresh(transaction)

    return transaction


# =====================================================
# DELETE TRANSACTION
#
# Soft delete is preserved.
#
# Before deleting:
# Reverse the transaction's effect on the account.
# =====================================================

@router.delete(
    "/{transaction_id}"
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    # =================================================
    # FIND TRANSACTION
    # =================================================

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

    # =================================================
    # FIND ACCOUNT
    # =================================================

    account = (
        db.query(Account)
        .filter(
            Account.id == transaction.account_id,
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    # =================================================
    # CALCULATE TRANSACTION EFFECT
    # =================================================

    balance_effect = get_balance_effect(
        transaction.transaction_type,
        transaction.amount,
    )

    # =================================================
    # REVERSE TRANSACTION
    # =================================================

    account.current_balance -= balance_effect

    # =================================================
    # SOFT DELETE
    # =================================================

    transaction.is_deleted = True

    # =================================================
    # SAVE
    # =================================================

    db.commit()

    return {
        "message": "Transaction deleted successfully",
        "transaction_id": transaction_id,
    }
