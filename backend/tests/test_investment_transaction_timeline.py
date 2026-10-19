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

    # The locked parent query may select additional fields needed by the
    # cash-accounting logic; assert the lock ordering rather than an exact
    # SELECT projection.
    parent_lock = route_source.index("FROM investments")
    lock_clause = route_source.index("FOR UPDATE", parent_lock)
    ledger_timeline = route_source.index("SELECT id, transaction_type, quantity, transaction_date")
    assert parent_lock < lock_clause < ledger_timeline
