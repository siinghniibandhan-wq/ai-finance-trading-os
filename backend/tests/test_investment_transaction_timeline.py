from datetime import date
from decimal import Decimal

import pytest

from app.routes.investment_transactions import validate_transaction_timeline


def row(tx_id, tx_type, quantity, tx_date):
    return {
        "id": tx_id,
        "transaction_type": tx_type,
        "quantity": Decimal(str(quantity)),
        "transaction_date": date.fromisoformat(tx_date),
    }


def test_multiple_buys_and_partial_sales_keep_correct_remaining_quantity():
    rows = [
        row(1, "BUY", "10", "2026-01-01"),
        row(2, "BUY", "5", "2026-01-10"),
        row(3, "SELL", "4", "2026-01-15"),
    ]
    available, final_quantity = validate_transaction_timeline(
        rows, "SELL", Decimal("3"), date(2026, 1, 20)
    )
    assert available == Decimal("11")
    assert final_quantity == Decimal("8")


def test_backdated_sell_cannot_make_later_active_sell_invalid():
    rows = [
        row(1, "BUY", "10", "2026-01-01"),
        row(2, "SELL", "7", "2026-01-20"),
    ]
    with pytest.raises(ValueError, match="make holdings negative"):
        validate_transaction_timeline(
            rows, "SELL", Decimal("5"), date(2026, 1, 10)
        )


def test_sell_cannot_exceed_quantity_available_on_transaction_date():
    rows = [row(1, "BUY", "10", "2026-01-20")]
    with pytest.raises(ValueError, match="Insufficient holding quantity"):
        validate_transaction_timeline(
            rows, "SELL", Decimal("1"), date(2026, 1, 10)
        )


def test_backdated_buy_reconciles_existing_future_sell():
    rows = [row(1, "SELL", "4", "2026-01-20")]
    available, final_quantity = validate_transaction_timeline(
        rows, "BUY", Decimal("10"), date(2026, 1, 1)
    )
    assert available == Decimal("0")
    assert final_quantity == Decimal("6")


def test_create_transaction_locks_investment_row_before_validating_ledger():
    from pathlib import Path

    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "investment_transactions.py"
    ).read_text()
    create_route = source.split("# FIND INVESTMENT", 1)[1].split(
        "# VALIDATE THE COMPLETE ACTIVE LEDGER IN DATE ORDER", 1
    )[0]

    assert "FROM investments" in create_route
    assert "FOR UPDATE" in create_route

@pytest.mark.parametrize("route_name", ["update_transaction", "void_transaction"])
def test_edit_and_void_lock_parent_investment_before_reading_active_timeline(route_name):
    from pathlib import Path

    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "investment_transactions.py"
    ).read_text()
    route_start = source.index(f"def {route_name}(")
    route_end = source.find("\n@router.", route_start + 1)
    route_source = source[route_start:route_end if route_end != -1 else None]

    parent_lock = route_source.index("SELECT id, investment_account_id FROM investments")
    lock_clause = route_source.index("FOR UPDATE", parent_lock)
    ledger_timeline = route_source.index("SELECT id, transaction_type, quantity, transaction_date")
    assert parent_lock < lock_clause < ledger_timeline


def test_trade_cash_effect_uses_gross_buy_cost_and_net_sell_proceeds():
    from app.routes.investment_transactions import _cash_effect

    assert _cash_effect("BUY", Decimal("2"), Decimal("100"), Decimal("5")) == Decimal("-205")
    assert _cash_effect("SELL", Decimal("2"), Decimal("100"), Decimal("5")) == Decimal("195")


def test_investment_trade_routes_reconcile_cash_and_keep_audit_events():
    from pathlib import Path

    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "investment_transactions.py"
    ).read_text()

    assert "investment_account_id" in source
    assert "new_cash_effect - old_cash_effect" in source
    assert "_apply_cash_delta(db, broker_account, -original_cash_effect, user_id)" in source
    assert "entity_type=\"investment_transaction\"" in source
    assert "db.rollback()" in source


def test_sell_fees_cannot_exceed_gross_proceeds():
    from pathlib import Path

    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "investment_transactions.py"
    ).read_text()

    assert source.count("data.fees > data.quantity * data.price") == 2



@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", "1.0000001"),
        ("price", "10.00001"),
        ("fees", "0.001"),
    ],
)
def test_create_transaction_rejects_precision_database_would_round(field, value):
    from pydantic import ValidationError
    from app.routes.investment_transactions import InvestmentTransactionCreate

    payload = {
        "user_id": 1,
        "investment_id": 1,
        "transaction_type": "BUY",
        "quantity": "1",
        "price": "10",
        "fees": "0",
        "transaction_date": "2026-10-16",
    }
    payload[field] = value
    with pytest.raises(ValidationError):
        InvestmentTransactionCreate(**payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", "1.0000001"),
        ("price", "10.00001"),
        ("fees", "0.001"),
    ],
)
def test_update_transaction_rejects_precision_database_would_round(field, value):
    from pydantic import ValidationError
    from app.routes.investment_transactions import InvestmentTransactionUpdate

    payload = {
        "transaction_type": "BUY",
        "quantity": "1",
        "price": "10",
        "fees": "0",
        "transaction_date": "2026-10-16",
    }
    payload[field] = value
    with pytest.raises(ValidationError):
        InvestmentTransactionUpdate(**payload)



def test_apply_cash_delta_updates_balance_without_losing_decimal_precision():
    from types import SimpleNamespace
    from app.routes.investment_transactions import _apply_cash_delta

    class FakeDB:
        def __init__(self):
            self.statement = None
            self.params = None
            self.rolled_back = False

        def execute(self, statement, params):
            self.statement = str(statement)
            self.params = params

        def rollback(self):
            self.rolled_back = True

    db = FakeDB()
    account = SimpleNamespace(id=7, balance=Decimal("100.25"))
    _apply_cash_delta(db, account, Decimal("-20.10"), user_id=3)

    assert db.params == {"balance": Decimal("80.15"), "account_id": 7, "user_id": 3}
    assert not db.rolled_back


def test_apply_cash_delta_rolls_back_when_debit_would_overdraw():
    from types import SimpleNamespace
    from fastapi import HTTPException
    from app.routes.investment_transactions import _apply_cash_delta

    class FakeDB:
        def __init__(self):
            self.executed = False
            self.rolled_back = False

        def execute(self, statement, params):
            self.executed = True

        def rollback(self):
            self.rolled_back = True

    db = FakeDB()
    account = SimpleNamespace(id=7, balance=Decimal("10.00"))
    with pytest.raises(HTTPException) as exc:
        _apply_cash_delta(db, account, Decimal("-10.01"), user_id=3)

    assert exc.value.status_code == 409
    assert db.rolled_back
    assert not db.executed
