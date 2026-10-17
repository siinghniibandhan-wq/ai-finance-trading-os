"""Reconcile confirmed broker trade-book fills into the Portfolio investment ledger.

Only trade-book executions carrying this user's Financial OS client_reference are
eligible. Order-book acknowledgements are never treated as fills.
"""
import os
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User
from app.routes.auth import get_current_user
from app.routes.broker_orders import _gateway_request
from app.routes.investment_transactions import ensure_transaction_table, validate_transaction_timeline
from app.routes.investments import ensure_investments_table

router = APIRouter(prefix="/api/broker-orders", tags=["Broker Order Reconciliation"])
TRADE_BOOK_PATH = os.getenv("MSTOCK_GATEWAY_TRADE_BOOK_PATH", "/trades")


def _trade_rows(response):
    """Accept only a documented list-shaped trade book; never infer fills from orders."""
    candidates = [response.get("trades"), response.get("tradebook"), response.get("data")]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            for key in ("trades", "tradebook", "items"):
                if isinstance(candidate.get(key), list):
                    return candidate[key]
    raise HTTPException(status_code=502, detail="Trade-book response has an unsupported shape; no portfolio records were changed.")


def _normalize_trade(row):
    if not isinstance(row, dict):
        return None
    trade_id = row.get("trade_id") or row.get("tradeid") or row.get("tradeId") or row.get("fill_id") or row.get("trade_no")
    reference = row.get("client_reference") or row.get("clientReference")
    symbol = row.get("symbol") or row.get("tradingsymbol") or row.get("trading_symbol")
    side = row.get("side") or row.get("transaction_type") or row.get("transactionType") or row.get("transactiontype")
    quantity = row.get("quantity") or row.get("traded_quantity") or row.get("filled_quantity") or row.get("tradeqty")
    price = row.get("price") or row.get("trade_price") or row.get("average_price") or row.get("tradeprice")
    trade_date = row.get("trade_date") or row.get("tradeDate") or row.get("tradedate") or row.get("date")
    exchange = row.get("exchange") or row.get("exch")
    if not all((trade_id, reference, symbol, side, quantity, price, trade_date, exchange)):
        return None
    try:
        qty = Decimal(str(quantity))
        px = Decimal(str(price))
        # ISO date or ISO datetime only; reject ambiguous broker-local formats.
        parsed_date = date.fromisoformat(str(trade_date)[:10])
    except (InvalidOperation, ValueError, TypeError):
        return None
    side = str(side).strip().upper()
    exchange = str(exchange).strip().upper()
    if qty <= 0 or px <= 0 or side not in {"BUY", "SELL"} or exchange not in {"NSE", "BSE"}:
        return None
    return {
        "trade_id": str(trade_id).strip(),
        "client_reference": str(reference).strip(),
        "symbol": str(symbol).strip().upper(),
        "side": side,
        "quantity": qty,
        "price": px,
        "trade_date": parsed_date,
        "exchange": exchange,
    }


def _ensure_reconciliation_table(db):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS broker_reconciled_fills (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            broker_trade_id VARCHAR(150) NOT NULL,
            investment_transaction_id INTEGER NOT NULL,
            reconciled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, broker_trade_id)
        )
    """))
    db.commit()


@router.post("/reconcile")
def reconcile_broker_fills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import confirmed trade-book fills idempotently; skips ambiguous/unmapped fills."""
    user_id = current_user.id
    ensure_investments_table(db)
    ensure_transaction_table(db)
    _ensure_reconciliation_table(db)

    # The gateway must expose confirmed trades, not just the order book.
    response = _gateway_request(TRADE_BOOK_PATH, "GET")
    trades = _trade_rows(response)
    own_prefix = f"financial-os-{user_id}-"
    imported, duplicates, skipped = [], [], []

    for raw in trades:
        trade = _normalize_trade(raw)
        if not trade:
            skipped.append({"reason": "missing_or_invalid_fill_fields"})
            continue
        # The configured gateway may return a shared account trade book. Never
        # attribute a fill without this user's client reference.
        if not trade["client_reference"].startswith(own_prefix):
            continue

        try:
            existing_fill = db.execute(text("""
                SELECT id FROM broker_reconciled_fills
                WHERE user_id = :user_id AND broker_trade_id = :trade_id
            """), {"user_id": user_id, "trade_id": trade["trade_id"]}).first()
            if existing_fill:
                duplicates.append(trade["trade_id"])
                continue

            investment = db.execute(text("""
                SELECT id, quantity, name, investment_type
                FROM investments
                WHERE user_id = :user_id
                  AND UPPER(COALESCE(symbol, '')) = :symbol
                  AND UPPER(COALESCE(exchange, :exchange)) = :exchange
                ORDER BY id
                LIMIT 1
                FOR UPDATE
            """), {"user_id": user_id, "symbol": trade["symbol"], "exchange": trade["exchange"]}).first()

            if not investment:
                if trade["side"] == "SELL":
                    skipped.append({"trade_id": trade["trade_id"], "reason": "no_matching_portfolio_investment"})
                    continue
                # New BUY: create a zero-quantity shell; the ledger fill below
                # becomes the sole source of quantity and cost basis.
                created = db.execute(text("""
                    INSERT INTO investments
                      (user_id, name, investment_type, symbol, quantity, buy_price,
                       current_price, buy_date, broker, fees, notes, exchange)
                    VALUES
                      (:user_id, :name, 'Stock', :symbol, 0, :price,
                       :price, :trade_date, 'm.Stock', 0, 'Created from confirmed broker fill', :exchange)
                    RETURNING id, quantity, name, investment_type
                """), {
                    "user_id": user_id, "name": trade["symbol"], "symbol": trade["symbol"],
                    "price": trade["price"], "trade_date": trade["trade_date"], "exchange": trade["exchange"],
                }).first()
                investment = created

            # Never mix broker fills into a legacy/manual position that has a
            # nonzero opening quantity but no transaction ledger.
            ledger_count = db.execute(text("""
                SELECT COUNT(*) FROM investment_transactions
                WHERE user_id = :user_id AND investment_id = :investment_id AND status = 'ACTIVE'
            """), {"user_id": user_id, "investment_id": investment.id}).scalar() or 0
            if not ledger_count and Decimal(str(investment.quantity or 0)) > 0:
                skipped.append({"trade_id": trade["trade_id"], "reason": "legacy_position_needs_opening_ledger"})
                db.rollback()
                continue

            active_rows = db.execute(text("""
                SELECT id, transaction_type, quantity, transaction_date
                FROM investment_transactions
                WHERE user_id = :user_id AND investment_id = :investment_id AND status = 'ACTIVE'
                ORDER BY transaction_date, id
            """), {"user_id": user_id, "investment_id": investment.id}).fetchall()
            try:
                _, new_quantity = validate_transaction_timeline(
                    active_rows, trade["side"], trade["quantity"], trade["trade_date"]
                )
            except ValueError as exc:
                skipped.append({"trade_id": trade["trade_id"], "reason": str(exc)})
                db.rollback()
                continue

            tx = db.execute(text("""
                INSERT INTO investment_transactions
                  (user_id, investment_id, transaction_type, quantity, price, fees, transaction_date, notes)
                VALUES
                  (:user_id, :investment_id, :side, :quantity, :price, 0, :trade_date, :notes)
                RETURNING id
            """), {
                "user_id": user_id, "investment_id": investment.id, "side": trade["side"],
                "quantity": trade["quantity"], "price": trade["price"], "trade_date": trade["trade_date"],
                "notes": f"Confirmed m.Stock trade fill {trade['trade_id']} ({trade['exchange']})",
            }).first()
            db.execute(text("""
                UPDATE investments
                SET quantity = :quantity, current_price = :price, updated_at = CURRENT_TIMESTAMP
                WHERE id = :investment_id AND user_id = :user_id
            """), {"quantity": new_quantity, "price": trade["price"], "investment_id": investment.id, "user_id": user_id})
            db.execute(text("""
                INSERT INTO broker_reconciled_fills (user_id, broker_trade_id, investment_transaction_id)
                VALUES (:user_id, :trade_id, :transaction_id)
            """), {"user_id": user_id, "trade_id": trade["trade_id"], "transaction_id": tx.id})
            db.commit()
            imported.append({"trade_id": trade["trade_id"], "investment_transaction_id": tx.id, "side": trade["side"], "quantity": str(trade["quantity"]), "price": str(trade["price"])})
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            # Do not leak broker response details or falsely claim import.
            raise HTTPException(status_code=500, detail="Fill reconciliation failed safely; check Portfolio History before retrying.")

    return {
        "status": "success",
        "imported_count": len(imported),
        "duplicate_count": len(duplicates),
        "skipped_count": len(skipped),
        "imported": imported,
        "duplicates": duplicates,
        "skipped": skipped,
        "message": "Only confirmed trade-book fills were imported. Orders and unconfirmed acknowledgements were not treated as executions.",
    }
