-- Financial OS: confirmed m.Stock broker-fill reconciliation
-- Review and apply manually only after verifying the Neon backup branch.
-- This migration creates a new table only; it does not alter existing tables.

BEGIN;

CREATE TABLE broker_reconciled_fills (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    broker_trade_id VARCHAR(150) NOT NULL,
    exchange_order_id VARCHAR(150) NOT NULL,
    client_reference VARCHAR(120) NOT NULL,
    investment_transaction_id INTEGER,
    reconciled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_broker_reconciled_fill_identity
        UNIQUE (user_id, broker_trade_id, exchange_order_id)
);

CREATE INDEX ix_broker_reconciled_fills_user_id
    ON broker_reconciled_fills (user_id);

CREATE INDEX ix_broker_reconciled_fills_exchange_order_id
    ON broker_reconciled_fills (exchange_order_id);

COMMIT;
