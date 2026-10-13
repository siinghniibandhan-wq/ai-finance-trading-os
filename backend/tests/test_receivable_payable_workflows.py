"""Receivable/payable creation and settlement API workflow tests."""
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Account, Category, Transaction, User
from app.schemas import TransactionCreate
from app.routes.transactions import create_transaction, settle_receivable_or_payable, SettlementCreate


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_receivable_partial_settlement_updates_bank_and_outstanding_without_new_income():
    db = make_session()
    user = User(name="RP workflow", currency="INR")
    db.add(user); db.flush()
    bank = Account(user_id=user.id, name="Bank", account_type="bank", currency="INR", balance=Decimal("500.00"))
    income = Category(user_id=user.id, name="Service Income", category_type="income")
    db.add_all([bank, income]); db.commit()
    item = create_transaction(TransactionCreate(
        user_id=user.id, account_id=bank.id, category_id=income.id,
        transaction_type="receivable", amount=Decimal("100.00"), transaction_date=date(2026, 10, 1),
        description="Invoice 1", party_name="Customer", due_date=date(2026, 10, 31),
    ), db, current_user=user)
    db.refresh(bank)
    assert bank.balance == Decimal("500.00")
    result = settle_receivable_or_payable(item.id, SettlementCreate(
        account_id=bank.id, amount=Decimal("40.00"), transaction_date=date(2026, 10, 12)
    ), db, current_user=user)
    db.refresh(item); db.refresh(bank)
    assert result["outstanding_amount"] == Decimal("60.00")
    assert item.settled_amount == Decimal("40.00")
    assert item.status == "partial"
    assert bank.balance == Decimal("540.00")
    assert db.query(Transaction).filter_by(user_id=user.id, transaction_type="income").count() == 0
    db.close()


def test_payable_partial_settlement_reduces_bank_and_payable_control():
    db = make_session()
    user = User(name="RP workflow", currency="INR")
    db.add(user); db.flush()
    bank = Account(user_id=user.id, name="Bank", account_type="bank", currency="INR", balance=Decimal("500.00"))
    expense = Category(user_id=user.id, name="Electricity", category_type="expense")
    db.add_all([bank, expense]); db.commit()
    item = create_transaction(TransactionCreate(
        user_id=user.id, account_id=bank.id, category_id=expense.id,
        transaction_type="payable", amount=Decimal("100.00"), transaction_date=date(2026, 10, 1),
        description="Bill 1", party_name="Utility", due_date=date(2026, 10, 31),
    ), db, current_user=user)
    result = settle_receivable_or_payable(item.id, SettlementCreate(
        account_id=bank.id, amount=Decimal("30.00"), transaction_date=date(2026, 10, 12)
    ), db, current_user=user)
    db.refresh(item); db.refresh(bank)
    assert result["outstanding_amount"] == Decimal("70.00")
    assert item.settled_amount == Decimal("30.00")
    assert item.status == "partial"
    assert bank.balance == Decimal("470.00")
    db.close()
