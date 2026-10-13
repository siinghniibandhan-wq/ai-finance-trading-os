"""Receivable/payable journal accounting regression tests."""
from decimal import Decimal
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Account, Category, ChartOfAccount, JournalEntry, JournalLine, Transaction, User
from app.accounting import sync_transaction_journal


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def assert_balanced(db, tx):
    entry = db.query(JournalEntry).filter_by(user_id=tx.user_id, transaction_id=tx.id).one()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    assert len(lines) == 2
    debit = sum((Decimal(str(line.debit)) for line in lines), Decimal("0"))
    credit = sum((Decimal(str(line.credit)) for line in lines), Decimal("0"))
    assert debit == credit == Decimal(str(tx.amount))


def test_receivable_posts_asset_and_income_without_bank_posting():
    db = make_session()
    user = User(name="Receivable test", currency="INR")
    db.add(user); db.flush()
    bank = Account(user_id=user.id, name="Main Bank", account_type="bank", balance=Decimal("0"))
    salary = Category(user_id=user.id, name="Service Income", category_type="income")
    db.add_all([bank, salary]); db.flush()
    tx = Transaction(user_id=user.id, account_id=bank.id, category_id=salary.id,
                     transaction_type="receivable", amount=Decimal("10000.00"),
                     description="Invoice", transaction_date=date(2026, 10, 1), party_name="Customer")
    db.add(tx); db.flush()
    sync_transaction_journal(db, tx)
    assert_balanced(db, tx)
    entry = db.query(JournalEntry).filter_by(transaction_id=tx.id).one()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    receivable = db.query(ChartOfAccount).filter_by(user_id=user.id, code="1110").one()
    assert any(line.chart_of_account_id == receivable.id and line.debit == Decimal("10000.00") for line in lines)
    assert bank.balance == Decimal("0")
    db.close()


def test_payable_posts_expense_and_liability_without_bank_posting():
    db = make_session()
    user = User(name="Payable test", currency="INR")
    db.add(user); db.flush()
    bank = Account(user_id=user.id, name="Main Bank", account_type="bank", balance=Decimal("0"))
    expense = Category(user_id=user.id, name="Electricity", category_type="expense")
    db.add_all([bank, expense]); db.flush()
    tx = Transaction(user_id=user.id, account_id=bank.id, category_id=expense.id,
                     transaction_type="payable", amount=Decimal("2000.00"),
                     description="Electricity bill", transaction_date=date(2026, 10, 1), party_name="Utility")
    db.add(tx); db.flush()
    sync_transaction_journal(db, tx)
    assert_balanced(db, tx)
    entry = db.query(JournalEntry).filter_by(transaction_id=tx.id).one()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    payable = db.query(ChartOfAccount).filter_by(user_id=user.id, code="2010").one()
    assert any(line.chart_of_account_id == payable.id and line.credit == Decimal("2000.00") for line in lines)
    assert bank.balance == Decimal("0")
    db.close()
