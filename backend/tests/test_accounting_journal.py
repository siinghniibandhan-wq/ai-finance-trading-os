"""Persistent double-entry journal tests."""
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Account, Category, JournalEntry, JournalLine, Transaction, User
from app.accounting import sync_transaction_journal


def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def setup_user(db):
    user = User(name="Ledger Test", currency="INR")
    db.add(user)
    db.flush()
    bank = Account(user_id=user.id, name="Main Bank", account_type="bank", balance=Decimal("0"))
    cash = Account(user_id=user.id, name="Cash", account_type="cash", balance=Decimal("0"))
    db.add_all([bank, cash])
    db.flush()
    return user, bank, cash


def make_tx(db, user, account, kind, amount, category=None, destination=None):
    tx = Transaction(
        user_id=user.id, account_id=account.id, category_id=category.id if category else None,
        transaction_type=kind, amount=Decimal(amount), description="Test transaction",
        transaction_date=date(2026, 10, 1), transfer_to_account_id=destination.id if destination else None,
    )
    db.add(tx)
    db.flush()
    return tx


def assert_balanced(db, tx):
    entry = db.query(JournalEntry).filter_by(user_id=tx.user_id, transaction_id=tx.id).one()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    assert len(lines) == 2
    assert sum((Decimal(str(line.debit)) for line in lines), Decimal("0")) == sum(
        (Decimal(str(line.credit)) for line in lines), Decimal("0")
    )
    assert sum((Decimal(str(line.debit)) for line in lines), Decimal("0")) == Decimal(str(tx.amount))


def test_income_and_expense_post_balanced_journals():
    db = session()
    user, bank, _ = setup_user(db)
    salary = Category(user_id=user.id, name="Salary", category_type="income")
    groceries = Category(user_id=user.id, name="Groceries", category_type="expense")
    db.add_all([salary, groceries])
    db.flush()

    income = make_tx(db, user, bank, "income", "50000.00", salary)
    sync_transaction_journal(db, income)
    assert_balanced(db, income)
    income_lines = db.query(JournalLine).filter_by(journal_entry_id=1).all()
    assert any(line.credit == Decimal("50000.00") for line in income_lines)

    expense = make_tx(db, user, bank, "expense", "2500.00", groceries)
    sync_transaction_journal(db, expense)
    assert_balanced(db, expense)
    db.close()


def test_transfer_posts_destination_debit_and_source_credit():
    db = session()
    user, bank, cash = setup_user(db)
    tx = make_tx(db, user, bank, "transfer", "1000.00", destination=cash)
    sync_transaction_journal(db, tx)
    assert_balanced(db, tx)
    entry = db.query(JournalEntry).filter_by(transaction_id=tx.id).one()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    assert any(line.financial_account_id == cash.id and line.debit == Decimal("1000.00") for line in lines)
    assert any(line.financial_account_id == bank.id and line.credit == Decimal("1000.00") for line in lines)
    db.close()


def test_loan_disbursement_is_credited_to_liability_not_income():
    db = session()
    user, bank, _ = setup_user(db)
    loan_category = Category(user_id=user.id, name="Loan Disbursement", category_type="income")
    db.add(loan_category)
    db.flush()
    tx = make_tx(db, user, bank, "income", "20000.00", loan_category)
    sync_transaction_journal(db, tx)
    assert_balanced(db, tx)
    entry = db.query(JournalEntry).filter_by(transaction_id=tx.id).one()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    liability = db.query(__import__("app.models", fromlist=["ChartOfAccount"]).ChartOfAccount).filter_by(
        user_id=user.id, code="2030"
    ).one()
    assert any(line.chart_of_account_id == liability.id and line.credit == Decimal("20000.00") for line in lines)
    db.close()


def test_sync_is_idempotent():
    db = session()
    user, bank, _ = setup_user(db)
    tx = make_tx(db, user, bank, "income", "123.45")
    sync_transaction_journal(db, tx)
    sync_transaction_journal(db, tx)
    entries = db.query(JournalEntry).filter_by(transaction_id=tx.id).all()
    assert len(entries) == 1
    assert len(db.query(JournalLine).filter_by(journal_entry_id=entries[0].id).all()) == 2
    db.close()
