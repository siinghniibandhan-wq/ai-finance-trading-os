"""Regression coverage for cross-account transfers and permanent history."""
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Account, FinanceDiaryEntry, User
from app.schemas import TransactionCreate
from app.routes.transactions import create_transaction, delete_transaction


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_transfer_moves_money_between_accounts_without_income_or_expense():
    db = _session()
    user = User(name="Transfer Test", currency="INR")
    db.add(user)
    db.flush()
    source = Account(user_id=user.id, name="Bank", account_type="bank", currency="INR", balance=Decimal("10000"))
    destination = Account(user_id=user.id, name="Broker Cash", account_type="investment", currency="INR", balance=Decimal("0"))
    db.add_all([source, destination])
    db.commit()

    transaction = create_transaction(TransactionCreate(
        user_id=user.id, account_id=source.id, transfer_to_account_id=destination.id,
        transaction_type="transfer", amount=Decimal("2500"), transaction_date=date(2026, 10, 12),
        description="Fund broker account",
    ), db, current_user=user)

    db.refresh(source)
    db.refresh(destination)
    assert source.balance == Decimal("7500.00")
    assert destination.balance == Decimal("2500.00")
    assert transaction.transaction_type == "transfer"
    assert db.query(FinanceDiaryEntry).filter_by(entity_type="transfer", entity_id=str(transaction.id)).count() == 1

    delete_transaction(transaction.id, db, current_user=user)
    db.refresh(source)
    db.refresh(destination)
    assert source.balance == Decimal("10000.00")
    assert destination.balance == Decimal("0.00")
    assert db.query(FinanceDiaryEntry).filter_by(entity_type="transfer", entity_id=str(transaction.id)).count() == 2
    db.close()
