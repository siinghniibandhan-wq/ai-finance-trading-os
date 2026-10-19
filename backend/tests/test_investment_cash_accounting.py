from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

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
