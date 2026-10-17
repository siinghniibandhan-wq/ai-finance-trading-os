from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.routes.broker_reconciliation import _normalize_trade, _trade_rows


def test_normalize_confirmed_trade_fill():
    trade = _normalize_trade({
        "trade_id": "TRD-101",
        "client_reference": "financial-os-7-unique",
        "symbol": "reliance-eq",
        "side": "buy",
        "quantity": "2",
        "price": "1450.25",
        "trade_date": "2026-10-17T10:15:00",
        "exchange": "NSE",
    })
    assert trade["trade_id"] == "TRD-101"
    assert trade["symbol"] == "RELIANCE-EQ"
    assert trade["side"] == "BUY"
    assert trade["quantity"] == Decimal("2")
    assert trade["price"] == Decimal("1450.25")
    assert trade["trade_date"] == date(2026, 10, 17)


@pytest.mark.parametrize("row", [
    {"trade_id": "x", "symbol": "ABC", "side": "BUY", "quantity": 1, "price": 10, "trade_date": "2026-10-17", "exchange": "NSE"},
    {"trade_id": "x", "client_reference": "financial-os-7-a", "symbol": "ABC", "side": "BUY", "quantity": 0, "price": 10, "trade_date": "2026-10-17", "exchange": "NSE"},
    {"trade_id": "x", "client_reference": "financial-os-7-a", "symbol": "ABC", "side": "BUY", "quantity": 1, "price": 10, "trade_date": "17/10/2026", "exchange": "NSE"},
    {"trade_id": "x", "client_reference": "financial-os-7-a", "symbol": "ABC", "side": "BUY", "quantity": 1, "price": 10, "trade_date": "2026-10-17", "exchange": "MCX"},
])
def test_invalid_or_unattributable_fill_is_rejected(row):
    assert _normalize_trade(row) is None


def test_trade_book_accepts_documented_list_shapes():
    assert _trade_rows({"trades": [{"trade_id": "x"}]}) == [{"trade_id": "x"}]
    assert _trade_rows({"data": {"items": [{"trade_id": "x"}]}}) == [{"trade_id": "x"}]


def test_trade_book_rejects_unsupported_shape():
    with pytest.raises(HTTPException) as error:
        _trade_rows({"orders": [{"order_id": "not-a-fill"}]})
    assert error.value.status_code == 502


def test_normalize_mstock_style_tradebook_fields_with_gateway_mapping():
    trade = _normalize_trade({
        "tradeid": "TRD-2026-9",
        "client_reference": "financial-os-7-ref",
        "tradingsymbol": "INFY-EQ",
        "transactiontype": "BUY",
        "tradeqty": "3",
        "tradeprice": "1500.50",
        "tradedate": "2026-10-17",
        "exchange": "NSE",
    })
    assert trade is not None
    assert trade["trade_id"] == "TRD-2026-9"
    assert trade["symbol"] == "INFY-EQ"
    assert trade["side"] == "BUY"
    assert trade["quantity"] == Decimal("3")
    assert trade["price"] == Decimal("1500.50")
