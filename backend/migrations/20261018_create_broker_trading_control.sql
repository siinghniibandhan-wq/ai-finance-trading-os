-- Persistent Financial OS live-order kill switch. Absence of a row means OFF.
CREATE TABLE IF NOT EXISTS broker_trading_control (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_by INTEGER NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
