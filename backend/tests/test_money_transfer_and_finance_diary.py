"""Regression coverage for cross-account transfers and permanent history."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Account, Category, FinanceDiaryEntry, Transaction, User
from app.schemas import TransactionCreate
from app.routes.transactions import create_transaction, delete_transaction
from app.routes.finance_diary import finance_diary_daily_summary


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

def test_income_creation_and_deletion_are_recorded_in_finance_diary():
    db = _session()
    user = User(name="Diary Test", currency="INR")
    db.add(user)
    db.flush()
    account = Account(
        user_id=user.id, name="Bank", account_type="bank",
        currency="INR", balance=Decimal("1000"),
    )
    db.add(account)
    db.commit()

    transaction = create_transaction(TransactionCreate(
        user_id=user.id, account_id=account.id,
        transaction_type="income", amount=Decimal("500"),
        transaction_date=date(2026, 10, 22), description="Salary test",
    ), db, current_user=user)

    db.refresh(account)
    entries = db.query(FinanceDiaryEntry).filter_by(
        entity_type="transaction", entity_id=str(transaction.id)
    ).all()
    assert account.balance == Decimal("1500.00")
    assert len(entries) == 1
    assert entries[0].event_type == "created"

    delete_transaction(transaction.id, db, current_user=user)

    db.refresh(account)
    entries = db.query(FinanceDiaryEntry).filter_by(
        entity_type="transaction", entity_id=str(transaction.id)
    ).order_by(FinanceDiaryEntry.id.asc()).all()
    assert account.balance == Decimal("1000.00")
    assert [entry.event_type for entry in entries] == ["created", "deleted"]
    assert db.query(FinanceDiaryEntry).count() == 2
    db.close()



def test_daily_finance_diary_summary_excludes_transfers_and_refunds():
    db = _session()
    user = User(name="Daily Summary Test", currency="INR")
    db.add(user)
    db.flush()
    account = Account(user_id=user.id, name="Bank", account_type="bank", currency="INR", balance=Decimal("0"))
    salary = Category(user_id=user.id, name="Salary", category_type="income")
    food = Category(user_id=user.id, name="Food", category_type="expense")
    db.add_all([account, salary, food])
    db.flush()
    db.add_all([
        Transaction(user_id=user.id, account_id=account.id, category_id=salary.id, transaction_type="income", amount=Decimal("25000"), transaction_date=date(2026, 10, 22), description="Salary"),
        Transaction(user_id=user.id, account_id=account.id, category_id=food.id, transaction_type="expense", amount=Decimal("2000"), transaction_date=date(2026, 10, 22), description="Groceries"),
        Transaction(user_id=user.id, account_id=account.id, transaction_type="refund", amount=Decimal("300"), transaction_date=date(2026, 10, 22), description="Refund"),
        Transaction(user_id=user.id, account_id=account.id, transaction_type="transfer", amount=Decimal("1000"), transaction_date=date(2026, 10, 22), description="Own-account transfer"),
    ])
    db.add(FinanceDiaryEntry(
        user_id=user.id, event_type="created", entity_type="investment", entity_id="42",
        description="Investment position created",
        snapshot_json='{"quantity": "2", "buy_price": "500", "fees": "10"}',
        created_at=datetime(2026, 10, 22, 10, 0, 0),
    ))
    db.commit()

    result = finance_diary_daily_summary(
        start_date=date(2026, 10, 22), end_date=date(2026, 10, 22),
        db=db, current_user=user,
    )
    assert len(result) == 1
    day = result[0]
    assert day["total_income"] == "25000.00"
    assert day["total_expense"] == "2000.00"
    assert day["total_investment"] == "1010.00"
    assert day["income_by_source"] == {"Salary": "25000.00"}
    assert day["expense_by_category"] == {"Food": "2000.00"}
    db.close()
