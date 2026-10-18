"""Import confirmed m.Stock trade-book fills into the investment ledger.

The gateway must enrich each trade-book row with client_reference only when its
EXCH_ORDER_NUMBER exactly matches a broker order's exchange_order_id and that
broker order is mapped to a locally logged client_id. Never infer ownership from
symbol, quantity, price, tag, or timestamps.
"""
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import User
from app.routes.auth import get_current_admin
from app.routes.broker_orders import _gateway_request
from app.routes.investment_transactions import validate_transaction_timeline

router = APIRouter(prefix="/api/broker-orders", tags=["Broker Order Reconciliation"])
TRADE_BOOK_PATH = os.getenv("MSTOCK_GATEWAY_TRADE_BOOK_PATH", "/tradebook")


class _SkipFill(Exception):
    """Rollback this fill's savepoint without aborting other valid fills."""


def _trade_rows(response):
    if not isinstance(response, dict) or response.get("status") == "error":
        raise HTTPException(status_code=502, detail="Gateway returned a trade-book error; no fills were imported.")
    for key in ("tradebook", "trades", "data", "items"):
        value = response.get(key)
        if isinstance(value, list) and all(isinstance(row, dict) for row in value):
            return value
        if isinstance(value, dict):
            for nested_key in ("tradebook", "trades", "items", "data"):
                nested = value.get(nested_key)
                if isinstance(nested, list) and all(isinstance(row, dict) for row in nested):
                    return nested
    raise HTTPException(status_code=502, detail="Trade-book response has an unsupported shape; no portfolio records were changed.")


def _parse_trade_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("missing trade date")
    for fmt in (None, "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y"):
        try:
            if fmt is None:
                return date.fromisoformat(raw[:10])
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError("unsupported trade date")


def _normalize_trade(row):
    """Normalize only actual trade-book identifiers; never use /trades tradingsymbol as holding symbol."""
    if not isinstance(row, dict):
        return None
    trade_id = row.get("trade_id") or row.get("TRADE_NUMBER") or row.get("tradeid") or row.get("fill_id")
    exchange_order_id = row.get("exchange_order_id") or row.get("EXCH_ORDER_NUMBER")
    # Distinct from exchange_order_id: only gateway-enriched data may provide
    # broker_order_id after joining the order book to the local placement log.
    broker_order_id = row.get("broker_order_id")
    client_reference = row.get("client_reference") or row.get("client_id")
    # Require SYMBOL (or gateway-normalized symbol) as the instrument code.
    # FULL_SYMBOL and /trades tradingsymbol are deliberately not fallback keys:
    # they may contain display names rather than the exact instrument identifier.
    symbol = row.get("symbol") or row.get("SYMBOL")
    side = row.get("side") or row.get("BUY_SELL") or row.get("transaction_type")
    quantity = row.get("quantity") or row.get("QUANTITY") or row.get("traded_quantity")
    price = row.get("price") or row.get("PRICE") or row.get("trade_price") or row.get("average_price")
    trade_date = row.get("trade_date") or row.get("TRADE_DATE") or row.get("ORDER_DATE_TIME") or row.get("date")
    exchange = row.get("exchange") or row.get("EXCHANGE")
    if not all((trade_id, exchange_order_id, broker_order_id, client_reference, symbol, side, quantity, price, trade_date)):
        return None
    try:
        qty = Decimal(str(quantity))
        px = Decimal(str(price))
        parsed_date = _parse_trade_date(trade_date)
    except (InvalidOperation, ValueError, TypeError):
        return None
    normalized_side = str(side).strip().upper()
    normalized_side = {"B": "BUY", "S": "SELL"}.get(normalized_side, normalized_side)
    normalized_exchange = str(exchange or "").strip().upper()
    normalized_symbol = str(symbol).strip().upper()
    # If FULL_SYMBOL is qualified (e.g. NSE:ABC-EQ), strip only the exchange prefix.
    if ":" in normalized_symbol:
        normalized_symbol = normalized_symbol.split(":", 1)[1]
    if (not str(trade_id).strip() or not str(exchange_order_id).strip()
            or qty <= 0 or px <= 0 or normalized_side not in {"BUY", "SELL"}
            or normalized_exchange not in {"NSE", "BSE"} or not normalized_symbol):
        return None
    return {
        "trade_id": str(trade_id).strip(),
        "exchange_order_id": str(exchange_order_id).strip(),
        "broker_order_id": str(broker_order_id).strip(),
        "client_reference": str(client_reference).strip(),
        "symbol": normalized_symbol,
        "side": normalized_side,
        "quantity": qty,
        "price": px,
        "trade_date": parsed_date,
        "exchange": normalized_exchange,
    }


@router.post("/reconcile")
def reconcile_broker_fills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Import confirmed fills only; each fill and its ledger mutation are atomic."""
    user_id = current_user.id
    response = _gateway_request(TRADE_BOOK_PATH, "GET")
    trades = _trade_rows(response)

    # Fail closed until the broker's placement order_id is verified to match
    # the order identifier exposed by the trade-book endpoint. Dry-run is the
    # default and must not write markers, ledger rows, or holding quantities.
    if os.getenv("MSTOCK_ORDER_ID_MAPPING_VERIFIED", "0") != "1":
        preview = []
        for raw in trades:
            trade = _normalize_trade(raw)
            if trade is None:
                preview.append({"status": "skipped", "reason": "missing_or_invalid_tradebook_fields"})
            else:
                preview.append({
                    "status": "would_match_only_if_order_id_mapping_verified",
                    "trade_id": trade["trade_id"],
                    "exchange_order_id": trade["exchange_order_id"],
                    "client_reference_present": bool(trade["client_reference"]),
                    "exchange": trade["exchange"],
                    "side": trade["side"],
                    "quantity": str(trade["quantity"]),
                    "trade_date": trade["trade_date"].isoformat(),
                })
        return {
            "status": "dry_run",
            "mapping_verified": False,
            "imported_count": 0,
            "preview_count": len(preview),
            "preview": preview,
            "message": "No portfolio records were changed. Verify the broker order-ID mapping before enabling imports.",
        }

    imported, duplicates, skipped = [], [], []

    for raw in trades:
        trade = _normalize_trade(raw)
        if not trade:
            skipped.append({"reason": "missing_or_invalid_tradebook_fields"})
            continue
        try:
            # A unique broker_trade_id is the final race-safe duplicate guard.
            # The marker, investment transaction, and holding update share a savepoint.
            with db.begin_nested():
                marker = db.execute(text("""
                    INSERT INTO broker_reconciled_fills
                      (user_id, broker_trade_id, exchange_order_id, client_reference)
                    VALUES (:user_id, :trade_id, :exchange_order_id, :client_reference)
                    ON CONFLICT (broker_trade_id) DO NOTHING
                    RETURNING id
                """), {
                    "user_id": user_id, "trade_id": trade["trade_id"],
                    "exchange_order_id": trade["exchange_order_id"],
                    "client_reference": trade["client_reference"],
                }).first()
                if marker is None:
                    duplicates.append(trade["trade_id"])
                    raise _SkipFill()

                # The gateway's client_reference is not trusted on its own:
                # verify it belongs to this user in the backend's durable order table.
                submission = db.execute(text("""
                    SELECT id, investment_id, gateway_order_id, symbol, exchange, side, quantity
                    FROM broker_order_submissions
                    WHERE user_id = :user_id AND client_id = :client_reference
                    FOR UPDATE
                """), {"user_id": user_id, "client_reference": trade["client_reference"]}).first()
                # Never infer ownership or investment from symbol/price/time.
                # The documented broker order-ID mapping must be verified separately.
                if (
                    not submission
                    or not submission.gateway_order_id
                    or str(submission.gateway_order_id) != trade["broker_order_id"]
                    or not submission.investment_id
                    or (submission.exchange or "").upper() != trade["exchange"]
                    or (submission.side or "").upper() != trade["side"]
                    or not submission.quantity
                ):
                    raise _SkipFill()

                investment = db.execute(text("""
                    SELECT id, quantity, name
                    FROM investments
                    WHERE id = :investment_id AND user_id = :user_id
                    FOR UPDATE
                """), {"user_id": user_id, "investment_id": submission.investment_id}).first()

                if investment is None:
                    raise _SkipFill()

                already_filled = db.execute(text("""
                    SELECT COALESCE(SUM(it.quantity), 0)
                    FROM broker_reconciled_fills brf
                    JOIN investment_transactions it
                      ON it.id = brf.investment_transaction_id
                    WHERE brf.user_id = :user_id
                      AND brf.client_reference = :client_reference
                      AND brf.exchange_order_id = :exchange_order_id
                """), {
                    "user_id": user_id,
                    "client_reference": trade["client_reference"],
                    "exchange_order_id": trade["exchange_order_id"],
                }).scalar() or 0
                if Decimal(str(already_filled)) + trade["quantity"] > Decimal(str(submission.quantity)):
                    skipped.append({"trade_id": trade["trade_id"], "reason": "cumulative_fill_exceeds_order_quantity"})
                    raise _SkipFill()

                ledger_count = db.execute(text("""
                    SELECT COUNT(*) FROM investment_transactions
                    WHERE user_id = :user_id AND investment_id = :investment_id AND status = 'ACTIVE'
                """), {"user_id": user_id, "investment_id": investment.id}).scalar() or 0
                if not ledger_count and Decimal(str(investment.quantity or 0)) > 0:
                    # Do not merge broker fills into legacy/manual quantity without an opening ledger.
                    raise _SkipFill()

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
                    raise _SkipFill()

                tx = db.execute(text("""
                    INSERT INTO investment_transactions
                      (user_id, investment_id, transaction_type, quantity, price, fees, transaction_date, notes)
                    VALUES
                      (:user_id, :investment_id, :side, :quantity, :price, 0, :trade_date, :notes)
                    RETURNING id
                """), {
                    "user_id": user_id, "investment_id": investment.id, "side": trade["side"],
                    "quantity": trade["quantity"], "price": trade["price"], "trade_date": trade["trade_date"],
                    "notes": f"Confirmed m.Stock fill {trade['trade_id']} / exchange order {trade['exchange_order_id']}",
                }).first()
                db.execute(text("""
                    UPDATE investments
                    SET quantity = :quantity, current_price = :price, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :investment_id AND user_id = :user_id
                """), {
                    "quantity": new_quantity, "price": trade["price"],
                    "investment_id": investment.id, "user_id": user_id,
                })
                db.execute(text("""
                    UPDATE broker_reconciled_fills
                    SET investment_transaction_id = :transaction_id
                    WHERE id = :marker_id
                """), {"transaction_id": tx.id, "marker_id": marker.id})
                imported.append({
                    "trade_id": trade["trade_id"], "exchange_order_id": trade["exchange_order_id"],
                    "investment_transaction_id": tx.id, "side": trade["side"],
                    "quantity": str(trade["quantity"]), "price": str(trade["price"]),
                })
        except _SkipFill:
            # begin_nested rolls back only this fill; previously imported fills remain in session.
            if not any(item.get("trade_id") == trade["trade_id"] for item in skipped):
                skipped.append({"trade_id": trade["trade_id"], "reason": "unmatched_order_or_unsafe_position"})
            continue
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            # Log details server-side; never return broker response bodies or credentials.
            raise HTTPException(status_code=500, detail="Fill reconciliation failed safely; inspect Portfolio History before retrying.") from exc

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to commit reconciled fills; no partial import was retained.") from exc

    return {
        "status": "success",
        "imported_count": len(imported),
        "duplicate_count": len(duplicates),
        "skipped_count": len(skipped),
        "imported": imported,
        "duplicates": duplicates,
        "skipped": skipped,
        "message": "Only matched, confirmed trade-book fills were imported. Order acknowledgements were not treated as executions.",
    }
