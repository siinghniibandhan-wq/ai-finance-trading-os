# ============================================================
# TRANSACTIONS API
# ============================================================

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from uuid import uuid4

from app.database.database import get_db
from app.routes.auth import get_current_user
from app.models import (
    User, Account, Category, Transaction, Loan, Liability,
    LoanMovement, LoanReceivable, TaxSalaryIncomeRecord,
)
from app.finance_diary import record_finance_event
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
)


router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


def _financial_year_for_date(value):
    """Return Indian financial year label for a date."""
    if not value:
        return None
    start_year = value.year if value.month >= 4 else value.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _is_salary_category(db, category_id):
    if not category_id:
        return False
    category = db.query(Category).filter(Category.id == category_id).first()
    return bool(category and (category.name or "").strip().lower() == "salary")


def _invalidate_verified_salary_record(db, user_id, transaction_date):
    """Stop a separately verified salary snapshot overriding live transactions.

    Tax calculations prefer salary-category transactions. If one is edited or
    deleted, a verified standalone annual record can otherwise keep stale salary
    in the Tax Centre. Keep the record for audit, but return it to review.
    """
    financial_year = _financial_year_for_date(transaction_date)
    if not financial_year:
        return
    record = (
        db.query(TaxSalaryIncomeRecord)
        .filter_by(user_id=user_id, financial_year=financial_year, status="verified")
        .with_for_update()
        .first()
    )
    if record:
        record.status = "pending_review"



def _ensure_transfer_columns(db: Session):
    """Additive migration for older deployments; never rebuilds existing tables."""
    bind = db.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("transactions")}
    dialect = bind.dialect.name
    if "transfer_group_id" not in columns:
        db.execute(text("ALTER TABLE transactions ADD COLUMN transfer_group_id VARCHAR(36)"))
    if "transfer_to_account_id" not in columns:
        db.execute(text("ALTER TABLE transactions ADD COLUMN transfer_to_account_id INTEGER"))
    if dialect == "postgresql":
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_transfer_group_id ON transactions (transfer_group_id)"))
    db.commit()


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


LIABILITY_ACCOUNT_TYPES = {"loan", "credit_card", "credit line", "credit_line", "payable"}

def _apply_transfer_effect(source: Account, destination: Account, amount):
    """Apply transfer direction according to asset vs liability account semantics."""
    source_type = (source.account_type or "").strip().lower()
    destination_type = (destination.account_type or "").strip().lower()
    source_is_liability = source_type in LIABILITY_ACCOUNT_TYPES
    destination_is_liability = destination_type in LIABILITY_ACCOUNT_TYPES
    source.balance = (source.balance or 0) + amount if source_is_liability else (source.balance or 0) - amount
    destination.balance = (destination.balance or 0) - amount if destination_is_liability else (destination.balance or 0) + amount

def _reverse_transfer_effect(source: Account, destination: Account, amount):
    """Reverse a previously recorded transfer without creating income/expense."""
    source_type = (source.account_type or "").strip().lower()
    destination_type = (destination.account_type or "").strip().lower()
    source_is_liability = source_type in LIABILITY_ACCOUNT_TYPES
    destination_is_liability = destination_type in LIABILITY_ACCOUNT_TYPES
    source.balance = (source.balance or 0) - amount if source_is_liability else (source.balance or 0) + amount
    destination.balance = (destination.balance or 0) + amount if destination_is_liability else (destination.balance or 0) - amount


# ============================================================
# CREATE TRANSACTION
# ============================================================

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_transfer_columns(db)

    # --------------------------------------------------------
    # Check user
    # --------------------------------------------------------
    user = (
        db.query(User)
        .filter(User.id == current_user.id)
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
            Account.user_id == current_user.id,
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
                Category.user_id == current_user.id,
            )
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found for this user")

    # Transfers are a single source record with a destination account. Both
    # balances change atomically, while the record is excluded from income/expense.
    if transaction_data.transaction_type.strip().lower() == "transfer":
        if transaction_data.loan_details is not None:
            raise HTTPException(status_code=422, detail="Transfers cannot contain loan-disbursement details")
        if transaction_data.amount <= 0:
            raise HTTPException(status_code=422, detail="Transfer amount must be greater than zero")
        destination_id = transaction_data.transfer_to_account_id
        if destination_id is None or destination_id == account.id:
            raise HTTPException(status_code=422, detail="Choose a different destination account")
        destination = (db.query(Account).filter(Account.id == destination_id, Account.user_id == current_user.id).with_for_update().first())
        if destination is None:
            raise HTTPException(status_code=404, detail="Destination account not found for this user")
        transfer_group_id = str(uuid4())
        transaction = Transaction(
            user_id=current_user.id, account_id=account.id, category_id=None,
            transaction_type="transfer", amount=transaction_data.amount,
            description=transaction_data.description, transaction_date=transaction_data.transaction_date,
            reference=transaction_data.reference, transfer_group_id=transfer_group_id,
            transfer_to_account_id=destination.id,
        )
        try:
            _apply_transfer_effect(account, destination, transaction_data.amount)
            db.add(transaction)
            db.flush()
            record_finance_event(db, user_id=current_user.id, event_type="created", entity_type="transfer", entity_id=transaction.id, description=f"Transfer {transaction_data.amount} from {account.name} to {destination.name}", snapshot={"transaction_id": transaction.id, "transfer_group_id": transfer_group_id, "from_account_id": account.id, "from_account_name": account.name, "to_account_id": destination.id, "to_account_name": destination.name, "amount": transaction_data.amount, "date": transaction_data.transaction_date, "reference": transaction_data.reference})
            db.commit()
            db.refresh(transaction)
        except Exception:
            db.rollback()
            raise
        return transaction

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
                .filter(Category.user_id == current_user.id, Category.name.ilike("loan disbursement"))
                .first()
            )
            if category is None:
                category = Category(user_id=current_user.id, name="Loan Disbursement", category_type="income", description="Loan proceeds; not earned income")
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
    if transaction_data.transfer_to_account_id is not None:
        raise HTTPException(status_code=422, detail="Destination account is only valid for Transfer transactions")

    transaction = Transaction(
        user_id=current_user.id,
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
                user_id=current_user.id,
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
                user_id=current_user.id,
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
        _apply_balance_effect(account, transaction_data.transaction_type.lower(), transaction_data.amount)
        record_finance_event(db, user_id=current_user.id, event_type="created", entity_type="transaction", entity_id=transaction.id, description=f"Transaction created: {transaction.transaction_type} {transaction.amount}", snapshot={"id": transaction.id, "account_id": transaction.account_id, "category_id": transaction.category_id, "transaction_type": transaction.transaction_type, "amount": transaction.amount, "description": transaction.description, "transaction_date": transaction.transaction_date, "reference": transaction.reference})
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_transfer_columns(db)
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
    current_user: User = Depends(get_current_user),
):
    _ensure_transfer_columns(db)
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
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
    current_user: User = Depends(get_current_user),
):
    _ensure_transfer_columns(db)
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .with_for_update()
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if (transaction.transaction_type or "").lower() == "transfer":
        raise HTTPException(status_code=409, detail="Transfers cannot be edited in place. Record a correcting transfer so the full audit history remains intact.")

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
    update_data.pop("user_id", None)  # Ownership is determined by the authenticated session.
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

    # Snapshot old salary linkage before mutating the transaction.
    old_type = transaction.transaction_type
    old_amount = transaction.amount
    old_date = transaction.transaction_date
    old_was_salary = _is_salary_category(db, transaction.category_id) and str(old_type).lower() == "income"
    new_category_is_salary = _is_salary_category(db, new_category_id) and str(new_type).lower() == "income"

    try:
        # Reverse the old transaction first, then apply the new transaction.
        _reverse_balance_effect(old_account, old_type, old_amount)

        for field, value in update_data.items():
            setattr(transaction, field, value)

        _apply_balance_effect(new_account, str(new_type).lower(), new_amount)
        if old_was_salary:
            _invalidate_verified_salary_record(db, transaction.user_id, old_date)
        if new_category_is_salary:
            _invalidate_verified_salary_record(db, transaction.user_id, transaction.transaction_date)
        record_finance_event(db, user_id=transaction.user_id, event_type="updated", entity_type="transaction", entity_id=transaction.id, description=f"Transaction updated: {transaction.id}", snapshot={"before": {"account_id": old_account.id, "transaction_type": old_type, "amount": old_amount}, "after": update_data})
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
    current_user: User = Depends(get_current_user),
):
    _ensure_transfer_columns(db)
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
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

    was_salary_transaction = _is_salary_category(db, transaction.category_id) and str(transaction.transaction_type).lower() == "income"

    try:
        if was_salary_transaction:
            _invalidate_verified_salary_record(db, transaction.user_id, transaction.transaction_date)
        if account:
            if (transaction.transaction_type or "").lower() == "transfer":
                destination = db.query(Account).filter(Account.id == transaction.transfer_to_account_id, Account.user_id == transaction.user_id).with_for_update().first()
                if destination:
                    _reverse_transfer_effect(account, destination, transaction.amount)
                else:
                    # The destination may have been deactivated, but keep the
                    # source correction and immutable destination snapshot.
                    account.balance = (account.balance or 0) + transaction.amount
                record_finance_event(db, user_id=transaction.user_id, event_type="deleted", entity_type="transfer", entity_id=transaction.id, description="Transfer deleted; source and destination balances reversed; original details retained in diary", snapshot={"id": transaction.id, "from_account_id": transaction.account_id, "to_account_id": transaction.transfer_to_account_id, "amount": transaction.amount, "transfer_group_id": transaction.transfer_group_id, "reference": transaction.reference})
            else:
                _reverse_balance_effect(account, str(transaction.transaction_type).lower(), transaction.amount)
                record_finance_event(db, user_id=transaction.user_id, event_type="deleted", entity_type="transaction", entity_id=transaction.id, description="Transaction deleted; original details retained in Finance Diary", snapshot={"id": transaction.id, "account_id": transaction.account_id, "category_id": transaction.category_id, "transaction_type": transaction.transaction_type, "amount": transaction.amount, "description": transaction.description, "transaction_date": transaction.transaction_date, "reference": transaction.reference})
        db.delete(transaction)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Transaction deleted successfully"}
