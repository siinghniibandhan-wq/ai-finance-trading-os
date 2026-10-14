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
