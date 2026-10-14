from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.routes.investment_pnl import calculate_weighted_average


def tx(kind, quantity, price, fees="0"):
    return SimpleNamespace(
        transaction_type=kind,
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)),
        fees=Decimal(str(fees)),
    )


def test_multiple_buys_partial_sale_and_remaining_cost_basis():
    result = calculate_weighted_average([
        tx("BUY", 10, 100),
        tx("BUY", 10, 120),
        tx("SELL", 15, 150),
    ])
    assert result["remaining_quantity"] == Decimal("5.000000")
    assert result["remaining_cost_basis"] == Decimal("550.00")
    assert result["realised_pnl"] == Decimal("600.00")
    assert result["total_sold_quantity"] == Decimal("15.000000")


def test_buy_and_sell_fees_are_included_in_pnl():
    result = calculate_weighted_average([
        tx("BUY", 10, 100, "10"),
        tx("SELL", 4, 120, "2"),
    ])
    assert result["remaining_quantity"] == Decimal("6.000000")
    assert result["remaining_cost_basis"] == Decimal("606.00")
    assert result["realised_pnl"] == Decimal("74.00")
    assert result["total_fees"] == Decimal("12.00")


def test_sell_cannot_exceed_available_quantity():
    with pytest.raises(ValueError, match="exceeds available holding"):
        calculate_weighted_average([
            tx("BUY", 3, 100),
            tx("SELL", 4, 120),
        ])


def test_rebuy_after_fully_closing_position_starts_new_cost_basis():
    result = calculate_weighted_average([
        tx("BUY", 2, 100),
        tx("SELL", 2, 120),
        tx("BUY", 3, 80),
    ])
    assert result["remaining_quantity"] == Decimal("3.000000")
    assert result["remaining_cost_basis"] == Decimal("240.00")
    assert result["realised_pnl"] == Decimal("40.00")
