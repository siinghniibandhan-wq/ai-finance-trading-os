# ============================================================
# FINANCIAL OS — ACCOUNTS API (NO AUTHENTICATION)
# Existing database tables and account records are preserved.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account, User
from app.routes.auth import get_current_user
from app.finance_diary import record_finance_event
from app.schemas import AccountCreate, AccountResponse, AccountUpdate

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse)
def create_account(account_data: AccountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create an account using the user_id supplied by the application."""
    normalized_type = (account_data.account_type or "").strip().lower()
    is_credit_account = normalized_type in {"credit_card", "credit_line", "credit line"}
    if is_credit_account:
        if account_data.credit_limit is None or account_data.credit_limit <= 0:
            raise HTTPException(status_code=422, detail="Credit Card and Credit Line accounts require a positive approved credit limit.")
        if account_data.balance < 0 or account_data.balance > account_data.credit_limit:
            raise HTTPException(status_code=422, detail="Opening outstanding amount must be between zero and the approved credit limit.")
    elif account_data.credit_limit is not None:
        raise HTTPException(status_code=422, detail="Credit limit is only valid for Credit Card or Credit Line accounts.")
    account = Account(
        user_id=current_user.id,
        name=account_data.name,
        account_type=account_data.account_type,
        institution=account_data.institution,
        account_number=account_data.account_number,
        currency=account_data.currency,
        balance=account_data.balance,
        credit_limit=account_data.credit_limit,
    )
    db.add(account)
    db.flush()
    record_finance_event(db, user_id=account.user_id, event_type="created", entity_type="account", entity_id=account.id, description=f"Account created: {account.name}", snapshot={"id": account.id, "name": account.name, "account_type": account.account_type, "institution": account.institution, "currency": account.currency, "balance": account.balance})
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=list[AccountResponse])
def list_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return only the authenticated customer's accounts."""
    return db.query(Account).filter(Account.user_id == current_user.id).order_by(Account.id.desc()).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(account_id: int, account_data: AccountUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    update_data = account_data.model_dump(exclude_unset=True)
    next_type = str(update_data.get("account_type", account.account_type) or "").strip().lower()
    next_limit = update_data.get("credit_limit", account.credit_limit)
    next_balance = update_data.get("balance", account.balance)
    if next_type in {"credit_card", "credit_line", "credit line"}:
        if next_limit is None or next_limit <= 0:
            raise HTTPException(status_code=422, detail="Credit Card and Credit Line accounts require a positive approved credit limit.")
        if next_balance is not None and (next_balance < 0 or next_balance > next_limit):
            raise HTTPException(status_code=422, detail="Outstanding amount must be between zero and the approved credit limit.")
    elif next_limit is not None:
        raise HTTPException(status_code=422, detail="Credit limit is only valid for Credit Card or Credit Line accounts.")
    before = {"id": account.id, "name": account.name, "account_type": account.account_type, "institution": account.institution, "currency": account.currency, "balance": account.balance, "is_active": account.is_active}
    for field, value in update_data.items():
        setattr(account, field, value)
    record_finance_event(db, user_id=account.user_id, event_type="updated", entity_type="account", entity_id=account.id, description=f"Account updated: {account.name}", snapshot={"before": before, "after": update_data})
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    # Keep account rows as inactive so references and historical balances remain stable.
    account.is_active = False
    record_finance_event(db, user_id=account.user_id, event_type="deactivated", entity_type="account", entity_id=account.id, description=f"Account deactivated (not physically deleted): {account.name}", snapshot={"id": account.id, "name": account.name, "account_type": account.account_type, "balance": account.balance})
    db.commit()
    return {"status": "deactivated", "account_id": account_id, "history_preserved": True}
