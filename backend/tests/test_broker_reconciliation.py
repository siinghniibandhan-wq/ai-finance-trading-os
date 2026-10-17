from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.routes.broker_reconciliation import _normalize_trade, _parse_trade_date, _trade_rows


def test_normalizes_mstock_tradebook_fields_and_exchange_order_id():
    row = {
        "TRADE_NUMBER": "T-1001",
        "EXCH_ORDER_NUMBER": "EX-9001",
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "RELIANCE",
        "BUY_SELL": "B",
        "QUANTITY": "2",
        "PRICE": "1234.50",
        "ORDER_DATE_TIME": "2026-10-17 10:15:00",
        "EXCHANGE": "NSE",
    }
    normalized = _normalize_trade(row)
    assert normalized is not None
    assert normalized["trade_id"] == "T-1001"
    assert normalized["exchange_order_id"] == "EX-9001"
    assert normalized["symbol"] == "RELIANCE"
    assert normalized["side"] == "BUY"
    assert normalized["quantity"] == Decimal("2")
    assert normalized["price"] == Decimal("1234.50")
    assert normalized["trade_date"] == date(2026, 10, 17)


def test_does_not_use_tradingsymbol_company_name_as_holding_symbol():
    row = {
        "TRADE_NUMBER": "T-1002",
        "EXCH_ORDER_NUMBER": "EX-9002",
        "client_reference": "financial-os-7-abc123",
        "tradingsymbol": "Reliance Industries Limited",
        "BUY_SELL": "B",
        "QUANTITY": "2",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17",
        "EXCHANGE": "NSE",
    }
    assert _normalize_trade(row) is None


def test_requires_exchange_order_id_and_trade_id():
    row = {
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "RELIANCE",
        "BUY_SELL": "B",
        "QUANTITY": "2",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17",
        "EXCHANGE": "NSE",
    }
    assert _normalize_trade(row) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-10-17", date(2026, 10, 17)),
        ("17-10-2026 10:15:00", date(2026, 10, 17)),
        ("17/10/2026", date(2026, 10, 17)),
    ],
)
def test_parse_trade_date(raw, expected):
    assert _parse_trade_date(raw) == expected


def test_rejects_http_200_error_payload_shape():
    with pytest.raises(HTTPException) as exc:
        _trade_rows({"status": "error", "message": "provider error"})
    assert exc.value.status_code == 502


def test_reads_nested_tradebook_rows():
    rows = [{"TRADE_NUMBER": "T-1"}]
    assert _trade_rows({"status": "success", "data": {"tradebook": rows}}) == rows
