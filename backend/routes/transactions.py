# =====================================================
# AI FINANCE TRADING OS
# TRANSACTIONS API
# =====================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Account, Category, Transaction
from database.schemas import (
    TransactionCreate,
    TransactionUpdate,
)


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


# =====================================================
# HELPER
# TRANSACTION BALANCE EFFECT
# =====================================================

def get_balance_effect(transaction_type, amount):
    """
    Determines how a transaction changes the account balance.

    Positive:
    - income
    - refund
    - interest
    - dividend

    Negative:
    - expense
    - withdrawal
    - tax
    - loan_repayment

    Zero:
    - transfer
    - investment
    - other
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

    return 0


# =====================================================
# HELPER
# TRANSACTION RESPONSE
# =====================================================

def transaction_to_dict(transaction):
    """
    Converts the SQLAlchemy Transaction object into a
    frontend-friendly dictionary.

    IMPORTANT:
    The existing database Transaction model does NOT
    contain a currency column.

    Therefore currency is supplied as INR for now.
    The frontend can continue using the currency field.
    """

    return {
        "id": transaction.id,
        "account_id": transaction.account_id,
        "category_id": transaction.category_id,
        "transaction_type": transaction.transaction_type,
        "amount": transaction.amount,
        "currency": "INR",
        "description": transaction.description,
        "merchant": transaction.merchant,
        "reference_number": transaction.reference_number,
        "transaction_date": transaction.transaction_date,
        "notes": transaction.notes,
    }


# =====================================================
# GET ALL TRANSACTIONS
# =====================================================

@router.get("/")
def get_transactions(
    db: Session = Depends(get_db),
):
    """
    Returns all active transactions.
    """

    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.is_deleted.is_(False)
        )
        .order_by(
            Transaction.transaction_date.desc()
        )
        .all()
    )

    return [
        transaction_to_dict(transaction)
        for transaction in transactions
    ]


# =====================================================
# GET SINGLE TRANSACTION
# =====================================================

@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns one transaction.
    """

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

    return transaction_to_dict(transaction)


# =====================================================
# CREATE TRANSACTION
# =====================================================

@router.post(
    "/",
    status_code=201,
)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new transaction.

    IMPORTANT:
    We intentionally DO NOT pass currency to the
    SQLAlchemy Transaction model because the existing
    database model does not contain that column.
    """

    # -------------------------------------------------
    # FIND ACCOUNT
    # -------------------------------------------------

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

    # -------------------------------------------------
    # VALIDATE CATEGORY
    # -------------------------------------------------

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

    # -------------------------------------------------
    # CREATE TRANSACTION
    # -------------------------------------------------
    #
    # DO NOT ADD:
    # currency=data.currency
    #
    # The existing Transaction model does not support it.
    # -------------------------------------------------

    transaction = Transaction(
        account_id=data.account_id,
        category_id=data.category_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        description=data.description,
        merchant=data.merchant,
        reference_number=data.reference_number,
        transaction_date=data.transaction_date,
        notes=data.notes,
    )

    db.add(transaction)

    # -------------------------------------------------
    # UPDATE ACCOUNT BALANCE
    # -------------------------------------------------

    balance_effect = get_balance_effect(
        data.transaction_type,
        data.amount,
    )

    account.current_balance += balance_effect

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    db.commit()
    db.refresh(transaction)

    return transaction_to_dict(transaction)


# =====================================================
# UPDATE TRANSACTION
# =====================================================

@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """
    Updates an existing transaction.

    Account balance is corrected when the transaction
    amount/type/account changes.
    """

    # -------------------------------------------------
    # FIND EXISTING TRANSACTION
    # -------------------------------------------------

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

    # -------------------------------------------------
    # SAVE OLD VALUES
    # -------------------------------------------------

    old_account = (
        db.query(Account)
        .filter(
            Account.id == transaction.account_id
        )
        .first()
    )

    old_effect = get_balance_effect(
        transaction.transaction_type,
        transaction.amount,
    )

    # -------------------------------------------------
    # PREPARE UPDATE DATA
    # -------------------------------------------------

    update_data = data.model_dump(
        exclude_unset=True
    )

    # -------------------------------------------------
    # VALIDATE NEW ACCOUNT
    # -------------------------------------------------

    new_account = old_account

    if "account_id" in update_data:

        new_account = (
            db.query(Account)
            .filter(
                Account.id == update_data["account_id"],
                Account.is_active.is_(True),
            )
            .first()
        )

        if not new_account:
            raise HTTPException(
                status_code=404,
                detail="Account not found",
            )

    # -------------------------------------------------
    # VALIDATE NEW CATEGORY
    # -------------------------------------------------

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

    # -------------------------------------------------
    # UPDATE TRANSACTION FIELDS
    # -------------------------------------------------

    for field, value in update_data.items():

        # ---------------------------------------------
        # IMPORTANT
        # ---------------------------------------------
        #
        # Currency exists in the frontend/schema but
        # NOT in the current SQLAlchemy model.
        #
        # Therefore do not attempt:
        #
        # transaction.currency = ...
        #
        # ---------------------------------------------

        if field == "currency":
            continue

        # Only update fields actually present on model.
        if hasattr(Transaction, field):
            setattr(
                transaction,
                field,
                value,
            )

    # -------------------------------------------------
    # CALCULATE NEW BALANCE EFFECT
    # -------------------------------------------------

    new_transaction_type = (
        update_data.get(
            "transaction_type",
            transaction.transaction_type,
        )
    )

    new_amount = (
        update_data.get(
            "amount",
            transaction.amount,
        )
    )

    new_effect = get_balance_effect(
        new_transaction_type,
        new_amount,
    )

    # -------------------------------------------------
    # REVERSE OLD BALANCE EFFECT
    # -------------------------------------------------

    if old_account:
        old_account.current_balance -= old_effect

    # -------------------------------------------------
    # APPLY NEW BALANCE EFFECT
    # -------------------------------------------------

    if new_account:
        new_account.current_balance += new_effect

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    db.commit()
    db.refresh(transaction)

    return transaction_to_dict(transaction)


# =====================================================
# DELETE TRANSACTION
# =====================================================

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Soft-deletes a transaction and reverses its
    account balance effect.
    """

    # -------------------------------------------------
    # FIND TRANSACTION
    # -------------------------------------------------

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

    # -------------------------------------------------
    # FIND ACCOUNT
    # -------------------------------------------------

    account = (
        db.query(Account)
        .filter(
            Account.id == transaction.account_id
        )
        .first()
    )

    # -------------------------------------------------
    # REVERSE BALANCE EFFECT
    # -------------------------------------------------

    if account:

        balance_effect = get_balance_effect(
            transaction.transaction_type,
            transaction.amount,
        )

        account.current_balance -= balance_effect

    # -------------------------------------------------
    # SOFT DELETE
    # -------------------------------------------------

    transaction.is_deleted = True

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    db.commit()

    return {
        "message": "Transaction deleted successfully",
        "transaction_id": transaction_id,
    }
