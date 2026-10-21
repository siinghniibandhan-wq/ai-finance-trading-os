# ============================================================
# TRANSACTIONS API
# ============================================================

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from uuid import uuid4

from app.database.database import get_db
from app.routes.auth import get_current_user
from app.models import (
    User, Account, Category, Transaction, Loan, Liability,
    LoanMovement, LoanReceivable, TaxSalaryIncomeRecord, JournalEntry, JournalLine,
)
from app.finance_diary import record_finance_event
from app.accounting import sync_transaction_journal, _get_control_account
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
    # Additive migration for receivable/payable tracking; safe for existing data.
    columns = {column["name"] for column in inspect(bind).get_columns("transactions")}
    additions = {
        "party_name": "VARCHAR(150)",
        "due_date": "DATE",
        "settled_amount": "NUMERIC(18, 2) NOT NULL DEFAULT 0",
        "status": "VARCHAR(20) NOT NULL DEFAULT 'open'",
        "settles_transaction_id": "INTEGER",
    }
    for name, definition in additions.items():
        if name not in columns:
            db.execute(text(f"ALTER TABLE transactions ADD COLUMN {name} {definition}"))
    if dialect == "postgresql":
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_settles_transaction_id ON transactions (settles_transaction_id)"))
    db.commit()


# ============================================================
# ACCOUNT BALANCE EFFECT
# Keep the sign rules in one place so create, edit, and delete
# apply exactly opposite effects when a transaction is reversed.
# ============================================================

INCREASE_BALANCE_TYPES = {"income", "refund", "interest", "dividend"}
DECREASE_BALANCE_TYPES = {"expense", "withdrawal", "tax", "loan_repayment"}


def _apply_balance_effect(account: Account, transaction_type: str, amount):
    """Apply transaction effects using liability balances as amounts owed."""
    is_liability = (account.account_type or "").strip().lower() in {"loan", "credit_card", "credit line", "credit_line", "payable"}
    if is_liability:
        if transaction_type in DECREASE_BALANCE_TYPES:
            account.balance = (account.balance or 0) + amount
        elif transaction_type in INCREASE_BALANCE_TYPES:
            account.balance = (account.balance or 0) - amount
    elif transaction_type in INCREASE_BALANCE_TYPES:
        account.balance = (account.balance or 0) + amount
    elif transaction_type in DECREASE_BALANCE_TYPES:
        account.balance = (account.balance or 0) - amount


def _reverse_balance_effect(account: Account, transaction_type: str, amount):
    """Reverse transaction effects using liability balances as amounts owed."""
    is_liability = (account.account_type or "").strip().lower() in {"loan", "credit_card", "credit line", "credit_line", "payable"}
    if is_liability:
        if transaction_type in DECREASE_BALANCE_TYPES:
            account.balance = (account.balance or 0) - amount
        elif transaction_type in INCREASE_BALANCE_TYPES:
            account.balance = (account.balance or 0) + amount
    elif transaction_type in INCREASE_BALANCE_TYPES:
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


class SettlementCreate(BaseModel):
    account_id: int = Field(gt=0, description="Bank/cash account receiving or making payment")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    transaction_date: date
    description: str | None = None
    reference: str | None = None


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
            sync_transaction_journal(db, transaction)
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

    tx_type = transaction_data.transaction_type.strip().lower()
    if tx_type not in {"income", "expense", "transfer", "receivable", "payable", "refund", "interest", "dividend", "withdrawal", "tax", "loan_repayment"}:
        raise HTTPException(status_code=422, detail="Unsupported transaction type")
    if tx_type in {"receivable", "payable"}:
        if category is None:
            raise HTTPException(status_code=422, detail="Choose an income category for a receivable or an expense category for a payable")
        expected = "income" if tx_type == "receivable" else "expense"
        if (category.category_type or "").strip().lower() != expected:
            raise HTTPException(status_code=422, detail=f"{tx_type.title()} requires a {expected} category")
        if transaction_data.transfer_to_account_id is not None:
            raise HTTPException(status_code=422, detail="Transfer destination is not valid for receivable/payable records")

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
        party_name=transaction_data.party_name,
        due_date=transaction_data.due_date,
        settled_amount=Decimal("0.00"),
        status="open",
    )

    try:
        db.add(transaction)
        db.flush()
        if tx_type in {"receivable", "payable"}:
            control = _get_control_account(db, current_user.id, tx_type)
            control.balance = (control.balance or Decimal("0.00")) + transaction_data.amount
        sync_transaction_journal(db, transaction)
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


@router.get("/receivables-payables")
def list_receivables_payables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return outstanding receivable/payable source records and totals."""
    _ensure_transfer_columns(db)
    rows = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type.in_(["receivable", "payable"]),
        )
        .order_by(Transaction.due_date.asc().nullslast(), Transaction.transaction_date.desc())
        .all()
    )
    items = []
    totals = {"receivable": Decimal("0.00"), "payable": Decimal("0.00")}
    for row in rows:
        outstanding = max(Decimal("0.00"), Decimal(str(row.amount)) - Decimal(str(row.settled_amount or 0)))
        if outstanding <= 0:
            continue
        kind = row.transaction_type.lower()
        totals[kind] += outstanding
        items.append({
            "id": row.id,
            "type": kind,
            "amount": Decimal(str(row.amount)),
            "settled_amount": Decimal(str(row.settled_amount or 0)),
            "outstanding_amount": outstanding,
            "party_name": row.party_name,
            "due_date": row.due_date,
            "transaction_date": row.transaction_date,
            "description": row.description,
            "status": row.status or ("partial" if row.settled_amount else "open"),
            "account_id": row.account_id,
            "category_id": row.category_id,
        })
    return {
        "items": items,
        "total_receivable": totals["receivable"],
        "total_payable": totals["payable"],
    }



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
    if (transaction.transaction_type or "").lower() in {"receivable", "payable"}:
        raise HTTPException(status_code=409, detail="Receivable/payable records cannot be edited in place. Create a correcting entry or manage settlement from the outstanding balance.")

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

    # Transfers must be created through the dedicated flow, which validates and
    # updates both accounts atomically. Never convert an ordinary transaction
    # into a transfer through this single-account edit endpoint.
    if str(new_type or "").strip().lower() == "transfer":
        raise HTTPException(
            status_code=409,
            detail="Transactions cannot be changed to Transfer in place. Create a new transfer using the Transfer form.",
        )

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
        sync_transaction_journal(db, transaction)
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

    if (transaction.transaction_type or "").lower() in {"receivable", "payable"} and Decimal(str(transaction.settled_amount or 0)) > 0:
        raise HTTPException(status_code=409, detail="This receivable/payable has settlements. It cannot be deleted because that would break the audit trail.")

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
        tx_type = (transaction.transaction_type or "").lower()
        if tx_type in {"receivable", "payable"}:
            control = _get_control_account(db, transaction.user_id, tx_type)
            control.balance = (control.balance or Decimal("0.00")) - Decimal(str(transaction.amount))
        if account:
            if (transaction.transaction_type or "").lower() == "transfer":
                destination = db.query(Account).filter(Account.id == transaction.transfer_to_account_id, Account.user_id == transaction.user_id).with_for_update().first()
                if destination:
                    _reverse_transfer_effect(account, destination, transaction.amount)
                else:
                    # The destination may have been deactivated, but keep the
                    # source correction and immutable destination snapshot.
                    account.balance = (account.balance or 0) + transaction.amount
            else:
                _reverse_balance_effect(account, str(transaction.transaction_type).lower(), transaction.amount)

        # Audit the deletion independently of balance reversal. A missing or
        # deactivated account must not silently erase the transaction history.
        if (transaction.transaction_type or "").lower() == "transfer":
            record_finance_event(
                db, user_id=transaction.user_id, event_type="deleted",
                entity_type="transfer", entity_id=transaction.id,
                description="Transfer deleted; original details retained in Finance Diary",
                snapshot={"id": transaction.id, "from_account_id": transaction.account_id,
                          "to_account_id": transaction.transfer_to_account_id,
                          "amount": transaction.amount, "transfer_group_id": transaction.transfer_group_id,
                          "reference": transaction.reference},
            )
        else:
            record_finance_event(
                db, user_id=transaction.user_id, event_type="deleted",
                entity_type="transaction", entity_id=transaction.id,
                description="Transaction deleted; original details retained in Finance Diary",
                snapshot={"id": transaction.id, "account_id": transaction.account_id,
                          "category_id": transaction.category_id, "transaction_type": transaction.transaction_type,
                          "amount": transaction.amount, "description": transaction.description,
                          "transaction_date": transaction.transaction_date, "reference": transaction.reference},
            )
        journal_ids = [
            row[0] for row in db.query(JournalEntry.id).filter_by(
                user_id=transaction.user_id, transaction_id=transaction.id
            ).all()
        ]
        if journal_ids:
            db.query(JournalLine).filter(
                JournalLine.journal_entry_id.in_(journal_ids)
            ).delete(synchronize_session=False)
            db.query(JournalEntry).filter(
                JournalEntry.id.in_(journal_ids), JournalEntry.user_id == transaction.user_id
            ).delete(synchronize_session=False)
        db.delete(transaction)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Transaction deleted successfully"}


@router.post("/{transaction_id}/settle")
def settle_receivable_or_payable(
    transaction_id: int,
    settlement: SettlementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a partial/full settlement as a transfer; never create new income/expense."""
    _ensure_transfer_columns(db)
    source = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
            Transaction.transaction_type.in_(["receivable", "payable"]),
        )
        .with_for_update()
        .first()
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Receivable/payable record not found")
    outstanding = Decimal(str(source.amount)) - Decimal(str(source.settled_amount or 0))
    amount = Decimal(str(settlement.amount)).quantize(Decimal("0.01"))
    if amount <= 0 or amount > outstanding:
        raise HTTPException(status_code=422, detail=f"Settlement must be greater than zero and no more than the outstanding amount ({outstanding})")

    cash_account = (
        db.query(Account)
        .filter(Account.id == settlement.account_id, Account.user_id == current_user.id, Account.is_active.is_(True))
        .with_for_update()
        .first()
    )
    if cash_account is None:
        raise HTTPException(status_code=404, detail="Selected bank/cash account not found for this user")

    control = _get_control_account(db, current_user.id, source.transaction_type.lower())
    if source.transaction_type.lower() == "receivable":
        from_account, to_account = control, cash_account
    else:
        from_account, to_account = cash_account, control

    settlement_tx = Transaction(
        user_id=current_user.id,
        account_id=from_account.id,
        category_id=None,
        transaction_type="transfer",
        amount=amount,
        description=settlement.description or f"Settlement for {source.party_name or source.description or source.transaction_type.title()}",
        transaction_date=settlement.transaction_date,
        reference=settlement.reference,
        transfer_group_id=str(uuid4()),
        transfer_to_account_id=to_account.id,
        settles_transaction_id=source.id,
        party_name=source.party_name,
        status="settled",
    )
    try:
        _apply_transfer_effect(from_account, to_account, amount)
        source.settled_amount = Decimal(str(source.settled_amount or 0)) + amount
        source.status = "settled" if source.settled_amount >= Decimal(str(source.amount)) else "partial"
        db.add(settlement_tx)
        db.flush()
        sync_transaction_journal(db, settlement_tx)
        record_finance_event(
            db, user_id=current_user.id, event_type="created", entity_type="receivable_payable_settlement",
            entity_id=settlement_tx.id,
            description=f"{source.transaction_type.title()} settlement of {amount}",
            snapshot={"source_transaction_id": source.id, "settlement_transaction_id": settlement_tx.id, "amount": str(amount), "outstanding_amount": str(Decimal(str(source.amount)) - source.settled_amount)},
        )
        db.commit()
        db.refresh(source)
        db.refresh(settlement_tx)
    except Exception:
        db.rollback()
        raise

    return {
        "source_transaction_id": source.id,
        "settlement_transaction_id": settlement_tx.id,
        "settled_amount": source.settled_amount,
        "outstanding_amount": Decimal(str(source.amount)) - source.settled_amount,
        "status": source.status,
    }
