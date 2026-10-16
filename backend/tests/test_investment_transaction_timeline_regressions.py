"""Focused regression coverage for investment-ledger timeline ordering and precision."""

from datetime import date
from decimal import Decimal

import pytest

from app.routes.investment_transactions import validate_transaction_timeline


def ledger_row(tx_id, tx_type, quantity, tx_date):
    return {
        "id": tx_id,
        "transaction_type": tx_type,
        "quantity": Decimal(str(quantity)),
        "transaction_date": date.fromisoformat(tx_date),
    }


def test_same_day_new_sell_is_ordered_after_existing_transactions():
    rows = [
        ledger_row(1, "BUY", "10", "2026-02-01"),
        ledger_row(2, "SELL", "4", "2026-02-10"),
    ]

    available, final_quantity = validate_transaction_timeline(
        rows, "SELL", Decimal("6"), date(2026, 2, 10)
    )

    assert available == Decimal("6")
    assert final_quantity == Decimal("0")


def test_same_day_sell_rejects_quantity_above_remaining_after_existing_sell():
    rows = [
        ledger_row(1, "BUY", "10", "2026-02-01"),
        ledger_row(2, "SELL", "7", "2026-02-10"),
    ]

    with pytest.raises(ValueError, match="Insufficient holding quantity"):
        validate_transaction_timeline(
            rows, "SELL", Decimal("4"), date(2026, 2, 10)
        )


def test_fractional_quantities_preserve_decimal_precision():
    rows = [
        ledger_row(1, "BUY", "1.250000", "2026-03-01"),
        ledger_row(2, "SELL", "0.200000", "2026-03-02"),
    ]

    available, final_quantity = validate_transaction_timeline(
        rows, "SELL", Decimal("0.300000"), date(2026, 3, 3)
    )

    assert available == Decimal("1.050000")
    assert final_quantity == Decimal("0.750000")


def test_full_sell_can_reduce_holding_exactly_to_zero():
    rows = [
        ledger_row(1, "BUY", "12.5", "2026-04-01"),
    ]

    available, final_quantity = validate_transaction_timeline(
        rows, "SELL", Decimal("12.5"), date(2026, 4, 2)
    )

    assert available == Decimal("12.5")
    assert final_quantity == Decimal("0.0")
