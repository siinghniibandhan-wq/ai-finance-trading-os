"""Regression tests for FIFO capital-gains lot consumption across tax years."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.routes import final_taxable_income as final_taxable_income
from app.routes import itr_ready_tax_report as itr_ready_tax_report


FY_START = date(2026, 4, 1)
FY_END = date(2027, 3, 31)


def _investment():
    return SimpleNamespace(
        id=1,
        name="Example Ltd",
        investment_type="stock",
        symbol="EXAMPLE",
    )


def _tx(tx_id, kind, qty, price, day, fees="0"):
    return SimpleNamespace(
        id=tx_id,
        investment_id=1,
        transaction_type=kind,
        quantity=Decimal(qty),
        price=Decimal(price),
        fees=Decimal(fees),
        transaction_date=day,
        notes=None,
    )


def _itr_tx(tx_id, kind, qty, price, day, fees="0"):
    return {
        "id": tx_id,
        "investment_id": 1,
        "transaction_type": kind,
        "quantity": Decimal(qty),
        "price": Decimal(price),
        "fees": Decimal(fees),
        "transaction_date": day,
    }


def test_final_taxable_income_consumes_prior_year_sell_before_current_year_sale(monkeypatch):
    transactions = [
        _tx(1, "BUY", "10", "10", date(2024, 1, 1)),
        _tx(2, "SELL", "8", "15", date(2025, 5, 1)),
        _tx(3, "BUY", "5", "20", date(2026, 5, 1)),
        _tx(4, "SELL", "5", "30", date(2026, 6, 1)),
    ]
    monkeypatch.setattr(final_taxable_income, "load_investments", lambda db, user_id: [_investment()])
    monkeypatch.setattr(final_taxable_income, "load_investment_transactions", lambda db, user_id: transactions)

    sales = final_taxable_income.calculate_capital_gains(None, 7, FY_START, FY_END)

    assert len(sales) == 1
    assert sales[0]["sale_transaction_id"] == 4
    assert sales[0]["matched_quantity"] == Decimal("5")
    assert sales[0]["cost_basis"] == Decimal("80.00")
    assert sales[0]["realised_gain_loss"] == Decimal("70.00")


def test_itr_report_consumes_prior_year_sell_before_current_year_sale(monkeypatch):
    transactions = [
        _itr_tx(1, "BUY", "10", "10", date(2024, 1, 1)),
        _itr_tx(2, "SELL", "8", "15", date(2025, 5, 1)),
        _itr_tx(3, "BUY", "5", "20", date(2026, 5, 1)),
        _itr_tx(4, "SELL", "5", "30", date(2026, 6, 1)),
    ]
    monkeypatch.setattr(itr_ready_tax_report, "load_investments", lambda db, user_id: [{
        "id": 1,
        "name": "Example Ltd",
        "investment_type": "stock",
        "symbol": "EXAMPLE",
    }])
    monkeypatch.setattr(itr_ready_tax_report, "load_investment_transactions", lambda db, user_id: transactions)

    result = itr_ready_tax_report.calculate_capital_gains(None, 7, FY_START, FY_END)

    assert len(result["sales"]) == 1
    assert result["sales"][0]["sale_transaction_id"] == 4
    assert result["sales"][0]["cost_basis"] == Decimal("80.00")
    assert result["sales"][0]["gain"] == Decimal("70.00")


def test_itr_report_does_not_match_future_buy_to_earlier_sale(monkeypatch):
    transactions = [
        _itr_tx(1, "BUY", "3", "10", date(2026, 5, 1)),
        _itr_tx(2, "SELL", "5", "20", date(2026, 6, 1)),
        _itr_tx(3, "BUY", "10", "5", date(2026, 7, 1)),
    ]
    monkeypatch.setattr(itr_ready_tax_report, "load_investments", lambda db, user_id: [{
        "id": 1,
        "name": "Example Ltd",
        "investment_type": "stock",
        "symbol": "EXAMPLE",
    }])
    monkeypatch.setattr(itr_ready_tax_report, "load_investment_transactions", lambda db, user_id: transactions)

    result = itr_ready_tax_report.calculate_capital_gains(None, 7, FY_START, FY_END)

    assert len(result["sales"]) == 1
    assert result["sales"][0]["matched_lots"][0]["quantity"] == Decimal("3.00")
    assert result["sales"][0]["unmatched_quantity"] == Decimal("2.00")
    assert result["sales"][0]["cost_basis"] == Decimal("30.00")


def test_final_taxable_income_only_counts_matched_quantity_and_allocates_sale_fees(monkeypatch):
    transactions = [
        _tx(1, "BUY", "3", "10", date(2026, 5, 1)),
        _tx(2, "SELL", "5", "20", date(2026, 6, 1), fees="10"),
    ]
    monkeypatch.setattr(final_taxable_income, "load_investments", lambda db, user_id: [_investment()])
    monkeypatch.setattr(final_taxable_income, "load_investment_transactions", lambda db, user_id: transactions)

    sales = final_taxable_income.calculate_capital_gains(None, 7, FY_START, FY_END)

    assert len(sales) == 1
    assert sales[0]["matched_quantity"] == Decimal("3")
    assert sales[0]["unmatched_quantity"] == Decimal("2")
    assert sales[0]["sale_proceeds"] == Decimal("60.00")
    assert sales[0]["sale_fees"] == Decimal("6.00")
    assert sales[0]["realised_gain_loss"] == Decimal("24.00")


def test_final_taxable_income_does_not_overallocate_buy_fees_across_partial_sales(monkeypatch):
    transactions = [
        _tx(1, "BUY", "10", "10", date(2026, 5, 1), fees="100"),
        _tx(2, "SELL", "5", "20", date(2026, 6, 1)),
        _tx(3, "SELL", "2", "20", date(2026, 7, 1)),
    ]
    monkeypatch.setattr(final_taxable_income, "load_investments", lambda db, user_id: [_investment()])
    monkeypatch.setattr(final_taxable_income, "load_investment_transactions", lambda db, user_id: transactions)

    sales = final_taxable_income.calculate_capital_gains(None, 7, FY_START, FY_END)

    assert len(sales) == 2
    assert sum((sale["cost_basis"] for sale in sales), Decimal("0")) == Decimal("140.00")


def test_final_taxable_income_classifies_each_fifo_lot_independently(monkeypatch):
    transactions = [
        _tx(1, "BUY", "1", "10", date(2025, 1, 1)),
        _tx(2, "BUY", "1", "10", date(2026, 5, 1)),
        _tx(3, "SELL", "2", "20", date(2026, 6, 1)),
    ]
    monkeypatch.setattr(final_taxable_income, "load_investments", lambda db, user_id: [_investment()])
    monkeypatch.setattr(final_taxable_income, "load_investment_transactions", lambda db, user_id: transactions)

    sales = final_taxable_income.calculate_capital_gains(None, 7, FY_START, FY_END)
    totals = final_taxable_income.calculate_capital_gain_totals(sales)

    assert len(sales) == 1
    assert sales[0]["classification"] == "MIXED"
    assert sales[0]["classification_breakdown"] == {"STCG": Decimal("10.00"), "LTCG": Decimal("10.00"), "UNCLASSIFIED": Decimal("0.00")}
    assert totals["stcg"] == Decimal("10.00")
    assert totals["ltcg"] == Decimal("10.00")



def test_final_taxable_income_uses_calendar_month_holding_period(monkeypatch):
    transactions = [
        _tx(1, "BUY", "1", "10", date(2025, 6, 1)),
        _tx(2, "SELL", "1", "20", date(2026, 6, 1)),
        _tx(3, "BUY", "1", "10", date(2025, 6, 1)),
        _tx(4, "SELL", "1", "20", date(2026, 6, 2)),
    ]
    monkeypatch.setattr(final_taxable_income, "load_investments", lambda db, user_id: [_investment()])
    monkeypatch.setattr(final_taxable_income, "load_investment_transactions", lambda db, user_id: transactions)

    sales = final_taxable_income.calculate_capital_gains(None, 7, FY_START, FY_END)

    assert len(sales) == 2
    # Exactly 12 calendar months is not "more than 12 months".
    assert sales[0]["matched_lots"][0]["classification"] == "STCG"
    assert sales[1]["matched_lots"][0]["classification"] == "LTCG"
