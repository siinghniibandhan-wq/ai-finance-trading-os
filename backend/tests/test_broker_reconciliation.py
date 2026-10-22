from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.routes.broker_reconciliation import _normalize_trade, _parse_trade_date, _submission_matches_trade, _trade_rows


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

@pytest.mark.parametrize("flag_value", ["true", "yes", "01", ""]) 
def test_reconciliation_requires_exact_mapping_flag_value_one(monkeypatch, flag_value):
    from types import SimpleNamespace
    from app.routes import broker_reconciliation

    monkeypatch.setenv("MSTOCK_ORDER_ID_MAPPING_VERIFIED", flag_value)
    monkeypatch.setattr(
        broker_reconciliation,
        "_gateway_request",
        lambda *args, **kwargs: {
            "status": "success",
            "data": [{
                "TRADE_NUMBER": "T-FLAG-1",
                "EXCH_ORDER_NUMBER": "EX-FLAG-1",
                "broker_order_id": "BROKER-FLAG-1",
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

    result = broker_reconciliation.reconcile_broker_fills(
        db=object(), current_user=SimpleNamespace(id=7)
    )

    assert result["status"] == "dry_run"
    assert result["mapping_verified"] is False
    assert result["imported_count"] == 0

@pytest.mark.parametrize("field", ["broker_order_id", "client_reference"])
def test_rejects_blank_normalized_order_references(field):
    row = {
        "TRADE_NUMBER": "T-BLANK-REF",
        "EXCH_ORDER_NUMBER": "EX-BLANK-REF",
        "broker_order_id": "BROKER-BLANK-REF",
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "RELIANCE",
        "BUY_SELL": "B",
        "QUANTITY": "1",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17 10:15:00",
        "EXCHANGE": "NSE",
    }
    row[field] = "   "
    assert _normalize_trade(row) is None




def test_submission_match_requires_exact_symbol_and_order_metadata():
    from types import SimpleNamespace
    from app.routes.broker_reconciliation import _submission_matches_trade

    trade = {
        "broker_order_id": "BROKER-1",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "side": "BUY",
    }
    submission = SimpleNamespace(
        status="ACKNOWLEDGED",
        gateway_order_id="BROKER-1",
        investment_id=10,
        symbol="RELIANCE",
        exchange="NSE",
        side="BUY",
        quantity=2,
    )
    assert _submission_matches_trade(submission, trade) is True

    submission.symbol = "TCS"
    assert _submission_matches_trade(submission, trade) is False


def test_submission_match_rejects_missing_symbol():
    from types import SimpleNamespace
    from app.routes.broker_reconciliation import _submission_matches_trade

    trade = {
        "broker_order_id": "BROKER-1",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "side": "BUY",
    }
    submission = SimpleNamespace(
        status="ACKNOWLEDGED",
        gateway_order_id="BROKER-1",
        investment_id=10,
        symbol=None,
        exchange="NSE",
        side="BUY",
        quantity=2,
    )
    assert _submission_matches_trade(submission, trade) is False

def test_normalizes_documented_mstock_trade_history_fields():
    # Mirrors the official Type A /trades schema. The gateway must enrich
    # broker_order_id/client_reference and supply the locally submitted symbol;
    # tradingsymbol may be a display name, not an instrument code.
    row = {
        "trade_id": "68346395",
        "order_id": "1300000040250500",
        "exchange_order_id": "1300000040250500",
        "exchange": "NSE",
        "symbol": "RCF",
        "tradingsymbol": "RASHTRIYA CHEMICALS & FER",
        "average_price": 145.45,
        "quantity": 1,
        "transaction_type": "SELL",
        "order_timestamp": "2024-02-14 14:48:23",
        "broker_order_id": "1300000040250500",
        "client_reference": "financial-os-7-abc123",
    }

    normalized = _normalize_trade(row)
    assert normalized is not None
    assert normalized["trade_id"] == "68346395"
    assert normalized["exchange_order_id"] == "1300000040250500"
    assert normalized["broker_order_id"] == "1300000040250500"
    assert normalized["symbol"] == "RCF"
    assert normalized["side"] == "SELL"
    assert normalized["quantity"] == Decimal("1")
    assert normalized["price"] == Decimal("145.45")
    assert normalized["trade_date"] == date(2024, 2, 14)

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("23-01-2025 02:55:55 PM", date(2025, 1, 23)),
        ("23-01-2025 02:55 PM", date(2025, 1, 23)),
        ("23/01/2025 02:55:55 PM", date(2025, 1, 23)),
    ],
)
def test_parse_documented_mstock_order_timestamp_formats(raw, expected):
    assert _parse_trade_date(raw) == expected

@pytest.mark.parametrize("field", ["QUANTITY", "PRICE"])
@pytest.mark.parametrize("bad_value", ["NaN", "Infinity", "-Infinity"])
def test_rejects_non_finite_broker_fill_values(field, bad_value):
    row = {
        "TRADE_NUMBER": "T-NON-FINITE",
        "EXCH_ORDER_NUMBER": "EX-NON-FINITE",
        "broker_order_id": "BROKER-NON-FINITE",
        "client_reference": "financial-os-7-abc123",
        "SYMBOL": "RELIANCE",
        "BUY_SELL": "B",
        "QUANTITY": "1",
        "PRICE": "100",
        "ORDER_DATE_TIME": "2026-10-17 10:15:00",
        "EXCHANGE": "NSE",
    }
    row[field] = bad_value
    assert _normalize_trade(row) is None


@pytest.mark.parametrize("status", ["ERROR", "Failed", " FAILURE "])
def test_rejects_case_insensitive_gateway_error_status(status):
    with pytest.raises(HTTPException) as exc:
        _trade_rows({"status": status, "data": []})
    assert exc.value.status_code == 502



@pytest.mark.parametrize("nested_status", ["ERROR", "Failed", " FAILURE "])
def test_rejects_nested_gateway_error_envelope(nested_status):
    # HTTP 200 may still contain a provider error in a nested response object.
    with pytest.raises(HTTPException) as exc:
        _trade_rows({
            "status": "success",
            "data": {
                "status": nested_status,
                "message": "provider rejected request",
                "data": None,
            },
        })
    assert exc.value.status_code == 502


def test_does_not_treat_trade_row_status_as_envelope_error():
    # A trade's own execution status is not the response-envelope status.
    rows = [{"TRADE_NUMBER": "T-2", "status": "Complete"}]
    assert _trade_rows({"status": "success", "data": rows}) == rows



def test_submission_match_requires_durable_broker_acknowledgement():
    from types import SimpleNamespace

    trade = {
        "broker_order_id": "BROKER-1",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "side": "BUY",
    }
    submission = SimpleNamespace(
        status="ACKNOWLEDGED",
        gateway_order_id="BROKER-1",
        investment_id=9,
        symbol="RELIANCE",
        exchange="NSE",
        side="BUY",
        quantity=2,
    )
    assert _submission_matches_trade(submission, trade) is True

    # A SUBMITTING reservation can exist even when a placement timed out;
    # never import a trade against that uncertain local state.
    submission.status = "SUBMITTING"
    assert _submission_matches_trade(submission, trade) is False


def test_submission_match_rejects_wrong_broker_order_id():
    from types import SimpleNamespace

    submission = SimpleNamespace(
        status="ACKNOWLEDGED",
        gateway_order_id="BROKER-OTHER",
        investment_id=9,
        symbol="RELIANCE",
        exchange="NSE",
        side="BUY",
        quantity=2,
    )
    trade = {
        "broker_order_id": "BROKER-1",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "side": "BUY",
    }
    assert _submission_matches_trade(submission, trade) is False


# Reconciliation uses the same date-ordered ledger validator as manual BUY/SELL.
# These tests cover partial fills and ensure a SELL cannot create negative holdings.
from app.routes.investment_transactions import validate_transaction_timeline


def test_reconciliation_timeline_allows_partial_buy_fills():
    rows = [
        {"id": 1, "transaction_type": "BUY", "quantity": Decimal("2"), "transaction_date": date(2026, 10, 17)},
    ]
    _, final_quantity = validate_transaction_timeline(
        rows, "BUY", Decimal("1.5"), date(2026, 10, 18)
    )
    assert final_quantity == Decimal("3.5")


def test_reconciliation_timeline_rejects_sell_above_available_holding():
    rows = [
        {"id": 1, "transaction_type": "BUY", "quantity": Decimal("2"), "transaction_date": date(2026, 10, 17)},
    ]
    with pytest.raises(ValueError, match="Insufficient holding quantity"):
        validate_transaction_timeline(
            rows, "SELL", Decimal("2.01"), date(2026, 10, 18)
        )


def test_reconciliation_timeline_rejects_sell_that_breaks_later_ledger():
    rows = [
        {"id": 1, "transaction_type": "BUY", "quantity": Decimal("5"), "transaction_date": date(2026, 10, 17)},
        {"id": 2, "transaction_type": "SELL", "quantity": Decimal("4"), "transaction_date": date(2026, 10, 20)},
    ]
    with pytest.raises(ValueError, match="negative on"):
        validate_transaction_timeline(
            rows, "SELL", Decimal("2"), date(2026, 10, 18)
        )


def test_reconciliation_timeline_respects_partial_sell_balance():
    rows = [
        {"id": 1, "transaction_type": "BUY", "quantity": Decimal("5"), "transaction_date": date(2026, 10, 17)},
        {"id": 2, "transaction_type": "SELL", "quantity": Decimal("1.25"), "transaction_date": date(2026, 10, 18)},
    ]
    _, final_quantity = validate_transaction_timeline(
        rows, "SELL", Decimal("1.75"), date(2026, 10, 19)
    )
    assert final_quantity == Decimal("2")


@pytest.mark.parametrize("envelope", [
    {"success": False, "data": []},
    {"error": "provider unavailable", "data": []},
    {"error_code": "E401", "data": []},
    {"data": {"success": False, "trades": []}},
    {"result": {"errorCode": "E500", "data": []}},
])
def test_rejects_false_success_and_error_code_tradebook_envelopes(envelope):
    with pytest.raises(HTTPException) as exc:
        _trade_rows(envelope)
    assert exc.value.status_code == 502


@pytest.mark.parametrize("value", [None, False, 0, "0", "false", "null", ""])
def test_allows_non_error_tradebook_error_flags(value):
    rows = [{"TRADE_NUMBER": "T-FLAG", "status": "Complete"}]
    response = {"success": True, "error": value, "data": rows}
    assert _trade_rows(response) == rows



def test_submission_match_supports_real_sqlalchemy_row():
    """Exercise the matcher with an actual SQLAlchemy Row, not a mock object."""
    from sqlalchemy import create_engine, text

    trade = {
        "broker_order_id": "BROKER-ROW-1",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "side": "BUY",
    }
    engine = create_engine("sqlite://")
    try:
        with engine.connect() as connection:
            row = connection.execute(text("""
                SELECT
                    'ACKNOWLEDGED' AS status,
                    'BROKER-ROW-1' AS gateway_order_id,
                    9 AS investment_id,
                    'RELIANCE' AS symbol,
                    'NSE' AS exchange,
                    'BUY' AS side,
                    2 AS quantity
            """)).first()
            assert row is not None
            assert _submission_matches_trade(row, trade) is True
            assert _submission_matches_trade(row._mapping, trade) is True
    finally:
        engine.dispose()
