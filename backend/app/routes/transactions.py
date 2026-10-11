# ============================================================
# TRANSACTIONS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import (
    User, Account, Category, Transaction, Loan, Liability,
    LoanMovement, LoanReceivable,
)
from app.routes.auth import get_current_user
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
    current_user: User = Depends(get_current_user),
):
        # SECURITY: Prevent creating transactions for another user.
    if transaction_data.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create transactions for another user.",
        )
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
    # Check category belongs to the same user. The special
    # Loan Disbursement category can be created on demand.
    # --------------------------------------------------------
    category = None
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
            raise HTTPException(status_code=404, detail="Category not found for this user")

    is_loan_disbursement = bool(
        category and (category.name or "").strip().lower() == "loan disbursement"
    ) or transaction_data.loan_details is not None

    if is_loan_disbursement:
        if transaction_data.transaction_type.lower() != "income":
            raise HTTPException(status_code=422, detail="Loan Disbursement must be recorded under Income")
        if transaction_data.loan_details is None:
            raise HTTPException(status_code=422, detail="Please complete the loan details for Loan Disbursement")
        if transaction_data.loan_details.principal_amount < transaction_data.amount:
            raise HTTPException(status_code=422, detail="Loan principal cannot be less than the amount received")
        if category is None:
            category = (
                db.query(Category)
                .filter(Category.user_id == transaction_data.user_id, Category.name.ilike("loan disbursement"))
                .first()
            )
            if category is None:
                category = Category(user_id=transaction_data.user_id, name="Loan Disbursement", category_type="income", description="Loan proceeds; not earned income")
                db.add(category)
                db.flush()
        elif (category.category_type or "").lower() != "income":
            raise HTTPException(status_code=422, detail="Loan Disbursement category must be an Income category")

    elif transaction_data.loan_details is not None:
        raise HTTPException(status_code=422, detail="Loan details are only allowed for Loan Disbursement")

    # --------------------------------------------------------
    # Create transaction; when this is a loan disbursement, also
    # create its loan and linked liability in the same DB commit.
    # --------------------------------------------------------
    if transaction_data.amount <= 0:
        raise HTTPException(status_code=422, detail="Transaction amount must be greater than zero")

    transaction = Transaction(
        user_id=transaction_data.user_id,
        account_id=transaction_data.account_id,
        category_id=category.id if category else None,
        transaction_type=transaction_data.transaction_type,
        amount=transaction_data.amount,
        description=transaction_data.description,
        transaction_date=transaction_data.transaction_date,
        reference=transaction_data.reference,
    )

    try:
        db.add(transaction)
        db.flush()
        if is_loan_disbursement:
            details = transaction_data.loan_details
            loan = Loan(
                user_id=transaction_data.user_id,
                name=details.name,
                lender_name=details.lender_name,
                loan_type=details.loan_type,
                principal_amount=details.principal_amount,
                amount_disbursed=transaction_data.amount,
                outstanding_principal=details.principal_amount,
                deposit_account_id=account.id,
                disbursement_transaction_id=transaction.id,
                interest_rate=details.interest_rate,
                interest_type=details.interest_type,
                tenure_months=details.tenure_months,
                emi_amount=details.emi_amount,
                start_date=transaction_data.transaction_date,
                first_payment_date=details.first_payment_date,
                repayment_frequency=details.repayment_frequency,
                processing_fee=details.processing_fee,
                reference_number=transaction_data.reference,
                notes=details.notes,
            )
            db.add(loan)
            db.flush()
            liability = Liability(
                user_id=transaction_data.user_id,
                name=details.name,
                liability_type=details.loan_type,
                original_amount=details.principal_amount,
                outstanding_amount=details.principal_amount,
                loan_id=loan.id,
                due_date=details.first_payment_date,
                notes=details.notes,
            )
            db.add(liability)

        # Income transaction increases the receiving account by the actual
        # amount received, not by the gross principal owed to the lender.
        _apply_balance_effect(account, transaction_data.transaction_type, transaction_data.amount)
        db.commit()
        db.refresh(transaction)
    except Exception:
        db.rollback()
        raise

    return transaction


# ============================================================
# GET TRANSACTIONS — AUTHENTICATED USER ONLY
# ============================================================

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Reject attempts to access another user's transactions.
    if user_id is not None and user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's transactions.",
        )

    # Return only the logged-in user's transactions.
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
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

    linked_loan = db.query(Loan).filter(Loan.disbursement_transaction_id == transaction.id).first()
    if linked_loan:
        raise HTTPException(
            status_code=409,
            detail="This transaction is linked to a loan. Edit loan terms in Loan Management; changing the disbursement transaction is disabled to protect account and liability consistency.",
        )

    # Loan repayments/recoveries are linked to principal and interest records.
    # Editing them here would desynchronize outstanding balances.
    linked_movement = (
        db.query(LoanMovement)
        .filter(LoanMovement.transaction_id == transaction.id)
        .first()
    )
    if linked_movement:
        raise HTTPException(
            status_code=409,
            detail="This transaction is linked to a loan repayment, recovery, or disbursement. Manage it through Loan Management so balances remain consistent.",
        )

    linked_receivable = (
        db.query(LoanReceivable)
        .filter(LoanReceivable.disbursement_transaction_id == transaction.id)
        .first()
    )
    if linked_receivable:
        raise HTTPException(
            status_code=409,
            detail="This transaction is linked to a loan given to another person. Manage it through Loan Management so the receivable balance remains consistent.",
        )

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

    linked_loan = db.query(Loan).filter(Loan.disbursement_transaction_id == transaction.id).first()
    if linked_loan:
        raise HTTPException(
            status_code=409,
            detail="This transaction is linked to a loan. Delete/cancel the loan through Loan Management first; direct transaction deletion is blocked to prevent an orphaned liability.",
        )

    linked_movement = (
        db.query(LoanMovement)
        .filter(LoanMovement.transaction_id == transaction.id)
        .first()
    )
    if linked_movement:
        raise HTTPException(
            status_code=409,
            detail="This transaction is linked to a loan repayment, recovery, or disbursement. Manage it through Loan Management so balances remain consistent.",
        )

    linked_receivable = (
        db.query(LoanReceivable)
        .filter(LoanReceivable.disbursement_transaction_id == transaction.id)
        .first()
    )
    if linked_receivable:
        raise HTTPException(
            status_code=409,
            detail="This transaction is linked to a loan given to another person. Manage it through Loan Management so the receivable balance remains consistent.",
        )

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
