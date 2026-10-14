from decimal import Decimal

from app.routes.holdings import build_holdings


def test_closed_position_retains_realised_pnl_for_portfolio_summary():
    investments = [{
        "id": 1,
        "user_id": 7,
        "name": "Example Ltd",
        "investment_type": "Stock",
        "symbol": "EXAMPLE",
        "quantity": Decimal("0"),
        "buy_price": Decimal("100"),
        "current_price": Decimal("150"),
        "broker": "Test Broker",
        "fees": Decimal("0"),
    }]
    transactions = [
        {"id": 1, "user_id": 7, "investment_id": 1,
         "transaction_type": "BUY", "quantity": Decimal("10"),
         "price": Decimal("100"), "fees": Decimal("0"),
         "transaction_date": "2026-01-01"},
        {"id": 2, "user_id": 7, "investment_id": 1,
         "transaction_type": "SELL", "quantity": Decimal("10"),
         "price": Decimal("150"), "fees": Decimal("0"),
         "transaction_date": "2026-02-01"},
    ]

    current_holdings = build_holdings(investments, transactions)
    all_positions = build_holdings(investments, transactions, include_closed=True)

    assert current_holdings == []
    assert len(all_positions) == 1
    assert all_positions[0]["quantity_held"] == Decimal("0")
    assert all_positions[0]["realised_gain_loss"] == Decimal("500")
    assert all_positions[0]["realised_cost_basis"] == Decimal("1000")
    assert all_positions[0]["unrealised_gain_loss"] == Decimal("0")


def test_open_position_still_appears_in_current_holdings():
    investments = [{
        "id": 2, "user_id": 7, "name": "Open Ltd",
        "investment_type": "Stock", "symbol": "OPEN",
        "quantity": Decimal("4"), "buy_price": Decimal("100"),
        "current_price": Decimal("110"), "broker": "Test Broker",
        "fees": Decimal("0"),
    }]
    transactions = [{
        "id": 3, "user_id": 7, "investment_id": 2,
        "transaction_type": "BUY", "quantity": Decimal("4"),
        "price": Decimal("100"), "fees": Decimal("0"),
        "transaction_date": "2026-01-01",
    }]

    holdings = build_holdings(investments, transactions)
    assert len(holdings) == 1
    assert holdings[0]["quantity_held"] == Decimal("4")
    assert holdings[0]["unrealised_gain_loss"] == Decimal("40")
