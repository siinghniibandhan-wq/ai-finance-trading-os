from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.routes.broker_reconciliation import _normalize_trade, _parse_trade_date, _trade_rows


def test_normalizes_mstock_tradebook_fields_and_exchange_order_id():
    row = {
        "TRADE_NUMBER": "T-1001",
        "EXCH_ORDER_NUMBER": "EX-9001",
        "broker_order_id": "BROKER-9001",
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
        "broker_order_id": "BROKER-9002",
        "client_reference": "financial-os-7-abc123",
        "tradingsymbol": "Reliance Industries Limited",
        "BUY_SELL": "B",
        "QUANTITY": "2",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17",
        "EXCHANGE": "NSE",
    }
    assert _normalize_trade(row) is None


def test_does_not_use_full_symbol_as_instrument_key():
    row = {
        "TRADE_NUMBER": "T-1003",
        "EXCH_ORDER_NUMBER": "EX-9003",
        "broker_order_id": "BROKER-9003",
        "client_reference": "financial-os-7-abc123",
        "FULL_SYMBOL": "NSE:RELIANCE-EQ",
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

def test_normalizes_documented_mstock_tradebook_sample():
    # Shape documented by m.Stock Type A tradebook API.
    row = {
        "TRADE_NUMBER": "206465040",
        "EXCH_ORDER_NUMBER": "1100000048872942",
        "broker_order_id": "1100000048872000",
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "IDEA",
        "FULL_SYMBOL": "VODAFONE IDEA LIMITED",
        "BUY_SELL": "Sell",
        "QUANTITY": 4,
        "PRICE": 6.98,
        "ORDER_DATE_TIME": "10-06-2025 13:08:42",
        "EXCHANGE": "NSE",
    }
    normalized = _normalize_trade(row)
    assert normalized is not None
    assert normalized["trade_id"] == "206465040"
    assert normalized["exchange_order_id"] == "1100000048872942"
    assert normalized["symbol"] == "IDEA"
    assert normalized["side"] == "SELL"
    assert normalized["quantity"] == Decimal("4")
    assert normalized["price"] == Decimal("6.98")
    assert normalized["trade_date"] == date(2025, 6, 10)




def test_reconciliation_defaults_to_dry_run_without_database_writes(monkeypatch):
    from types import SimpleNamespace
    from app.routes import broker_reconciliation

    monkeypatch.delenv("MSTOCK_ORDER_ID_MAPPING_VERIFIED", raising=False)
    monkeypatch.setattr(
        broker_reconciliation,
        "_gateway_request",
        lambda *args, **kwargs: {
            "status": "success",
            "data": [{
                "TRADE_NUMBER": "T-DRY-1",
                "EXCH_ORDER_NUMBER": "EX-DRY-1",
                "broker_order_id": "BROKER-DRY-1",
                "client_reference": "financial-os-7-test",
                "SYMBOL": "RELIANCE",
                "BUY_SELL": "B",
                "QUANTITY": "1",
                "PRICE": "100",
                "ORDER_DATE_TIME": "2026-10-17 10:15:00",
                "EXCHANGE": "NSE",
            }],
        },
    )

    # An opaque object proves the default path returns before any DB access.
    result = broker_reconciliation.reconcile_broker_fills(
        db=object(), current_user=SimpleNamespace(id=7)
    )

    assert result["status"] == "dry_run"
    assert result["mapping_verified"] is False
    assert result["imported_count"] == 0
    assert result["preview_count"] == 1
    assert result["preview"][0]["trade_id"] == "T-DRY-1"



def test_normalizer_keeps_broker_order_id_separate_from_exchange_order_id():
    row = {
        "TRADE_NUMBER": "T-ID-DISTINCT",
        "EXCH_ORDER_NUMBER": "EXCHANGE-123",
        "broker_order_id": "BROKER-456",
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "RELIANCE",
        "BUY_SELL": "B",
        "QUANTITY": "1",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17 10:15:00",
        "EXCHANGE": "NSE",
    }
    normalized = _normalize_trade(row)
    assert normalized is not None
    assert normalized["exchange_order_id"] == "EXCHANGE-123"
    assert normalized["broker_order_id"] == "BROKER-456"



def test_does_not_guess_broker_order_id_from_order_number():
    row = {
        "TRADE_NUMBER": "T-NO-GUESS",
        "EXCH_ORDER_NUMBER": "EXCHANGE-123",
        "ORDER_NUMBER": "POSSIBLY-EXCHANGE-ID",
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "RELIANCE",
        "BUY_SELL": "B",
        "QUANTITY": "1",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17 10:15:00",
        "EXCHANGE": "NSE",
    }
    assert _normalize_trade(row) is None
