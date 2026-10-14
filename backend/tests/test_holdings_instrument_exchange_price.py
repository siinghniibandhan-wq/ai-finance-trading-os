from datetime import datetime
from decimal import Decimal

from app.routes.holdings import build_holdings, holding_key


def _investment(i, *, symbol="RELIANCE", exchange="NSE", master_id=None,
                current_price="100", updated_at=None, quantity="2"):
    return {
        "id": i, "user_id": 7, "name": "Reliance Industries",
        "investment_type": "Stock", "symbol": symbol,
        "exchange": exchange, "instrument_master_id": master_id,
        "product_type": "Equity", "quantity": Decimal(quantity),
        "buy_price": Decimal("80"), "current_price": Decimal(current_price),
        "broker": f"Broker {i}", "fees": Decimal("0"),
        "updated_at": updated_at,
    }


def _buy(i, qty="2", price="80"):
    return {"id": i, "user_id": 7, "investment_id": i,
            "transaction_type": "BUY", "quantity": Decimal(qty),
            "price": Decimal(price), "fees": Decimal("0"),
            "transaction_date": "2026-01-01"}


def test_same_symbol_on_different_exchanges_stays_separate():
    nse = _investment(1, exchange="NSE", master_id=11)
    bse = _investment(2, exchange="BSE", master_id=22, current_price="101")
    result = build_holdings([nse, bse], [_buy(1), _buy(2)])
    assert len(result) == 2
    assert {row["exchange"] for row in result} == {"NSE", "BSE"}
    assert {row["current_value"] for row in result} == {Decimal("200"), Decimal("202")}


def test_same_master_instrument_uses_latest_updated_valid_price_and_flags_conflict():
    older = _investment(1, master_id=11, current_price="100",
                        updated_at=datetime(2026, 1, 1, 10, 0))
    newer = _investment(2, master_id=11, current_price="105",
                        updated_at=datetime(2026, 1, 2, 10, 0))
    result = build_holdings([older, newer], [_buy(1), _buy(2)])
    assert len(result) == 1
    assert result[0]["current_price"] == Decimal("105")
    assert result[0]["current_value"] == Decimal("420")
    assert result[0]["price_conflict"] is True


def test_fallback_identity_includes_exchange():
    assert holding_key(_investment(1, exchange="NSE")) != holding_key(
        _investment(2, exchange="BSE")
    )
