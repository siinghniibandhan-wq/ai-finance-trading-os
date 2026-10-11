# ============================================================
# FINANCIAL OS — ACCOUNTS API (NO AUTHENTICATION)
# Existing database tables and account records are preserved.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Account
from app.finance_diary import record_finance_event
from app.schemas import AccountCreate, AccountResponse, AccountUpdate

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse)
def create_account(account_data: AccountCreate, db: Session = Depends(get_db)):
    """Create an account using the user_id supplied by the application."""
    account = Account(
        user_id=account_data.user_id,
        name=account_data.name,
        account_type=account_data.account_type,
        institution=account_data.institution,
        account_number=account_data.account_number,
        currency=account_data.currency,
        balance=account_data.balance,
    )
    db.add(account)
    db.flush()
    record_finance_event(db, user_id=account.user_id, event_type="created", entity_type="account", entity_id=account.id, description=f"Account created: {account.name}", snapshot={"id": account.id, "name": account.name, "account_type": account.account_type, "institution": account.institution, "currency": account.currency, "balance": account.balance})
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=list[AccountResponse])
def list_accounts(user_id: int | None = None, db: Session = Depends(get_db)):
    """List all accounts, or filter by user_id when supplied."""
    query = db.query(Account)
    if user_id is not None:
        query = query.filter(Account.user_id == user_id)
    return query.order_by(Account.id.desc()).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(account_id: int, account_data: AccountUpdate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    update_data = account_data.model_dump(exclude_unset=True)
    before = {"id": account.id, "name": account.name, "account_type": account.account_type, "institution": account.institution, "currency": account.currency, "balance": account.balance, "is_active": account.is_active}
    for field, value in update_data.items():
        setattr(account, field, value)
    record_finance_event(db, user_id=account.user_id, event_type="updated", entity_type="account", entity_id=account.id, description=f"Account updated: {account.name}", snapshot={"before": before, "after": update_data})
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    # Keep account rows as inactive so references and historical balances remain stable.
    account.is_active = False
    record_finance_event(db, user_id=account.user_id, event_type="deactivated", entity_type="account", entity_id=account.id, description=f"Account deactivated (not physically deleted): {account.name}", snapshot={"id": account.id, "name": account.name, "account_type": account.account_type, "balance": account.balance})
    db.commit()
    return {"status": "deactivated", "account_id": account_id, "history_preserved": True}
