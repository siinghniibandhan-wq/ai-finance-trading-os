from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Account, User
from app.routes.accounts import delete_account, _has_linked_investments
from app.routes.investment_transactions import _apply_cash_delta, _cash_effect


class FakeSession:
    def __init__(self):
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((str(statement), params))


def test_buy_cash_effect_debits_purchase_and_fees():
    assert _cash_effect("BUY", Decimal("2"), Decimal("100.25"), Decimal("1.50")) == Decimal("-202.00")


def test_sell_cash_effect_credits_proceeds_after_fees():
    assert _cash_effect("SELL", Decimal("2"), Decimal("125.00"), Decimal("1.50")) == Decimal("248.50")


def test_cash_delta_updates_only_the_supplied_account():
    db = FakeSession()
    account = SimpleNamespace(id=42, balance=Decimal("500.00"))

    updated = _apply_cash_delta(db, account, Decimal("-120.25"))

    assert updated == Decimal("379.75")
    assert db.calls[-1][1] == {"balance": Decimal("379.75"), "account_id": 42}


def test_cash_delta_rejects_overdraw_without_writing():
    db = FakeSession()
    account = SimpleNamespace(id=42, balance=Decimal("50.00"))

    with pytest.raises(HTTPException) as error:
        _apply_cash_delta(db, account, Decimal("-50.01"))

    assert error.value.status_code == 409
    assert db.calls == []



def test_linked_investment_account_with_cash_and_open_position_cannot_be_deactivated():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    with SessionFactory() as db:
        user = User(name="Broker Account Guard Test", currency="INR")
        db.add(user)
        db.flush()
        account = Account(
            user_id=user.id,
            name="Broker Cash",
            account_type="Investment",
            balance=Decimal("1000.00"),
            is_active=True,
        )
        db.add(account)
        db.flush()
        db.execute(text("""
            CREATE TABLE investments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                investment_account_id INTEGER NOT NULL,
                quantity NUMERIC(18, 4) NOT NULL DEFAULT 0
            )
        """))
        db.execute(
            text("INSERT INTO investments (id, user_id, investment_account_id, quantity) VALUES (1, :user_id, :account_id, 10)"),
            {"user_id": user.id, "account_id": account.id},
        )
        db.commit()

        assert _has_linked_investments(db, user.id, account.id) is True
        with pytest.raises(HTTPException) as error:
            delete_account(account.id, db=db, current_user=user)

        assert error.value.status_code == 409
        db.refresh(account)
        assert account.is_active is True



def test_empty_linked_investment_account_can_be_closed_and_history_preserved():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    with SessionFactory() as db:
        user = User(name="Empty Broker Account Test", currency="INR")
        db.add(user)
        db.flush()
        account = Account(
            user_id=user.id,
            name="Old Broker Cash",
            account_type="Investment",
            balance=Decimal("0.00"),
            is_active=True,
        )
        db.add(account)
        db.flush()
        db.execute(text("""
            CREATE TABLE investments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                investment_account_id INTEGER NOT NULL,
                quantity NUMERIC(18, 4) NOT NULL DEFAULT 0
            )
        """))
        db.execute(text("""
            INSERT INTO investments (id, user_id, investment_account_id, quantity)
            VALUES (1, :user_id, :account_id, 0)
        """), {"user_id": user.id, "account_id": account.id})
        db.commit()

        result = delete_account(account.id, db=db, current_user=user)

        assert result == {"status": "deactivated", "account_id": account.id, "history_preserved": True}
        db.refresh(account)
        assert account.is_active is False
        assert db.execute(text("SELECT id FROM investments WHERE id = 1")).first() is not None
