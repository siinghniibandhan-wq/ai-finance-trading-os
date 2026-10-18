-- Add optional explicit investment linkage to durable broker submissions.
-- Review and apply manually; this migration is not applied by this commit.
BEGIN;

ALTER TABLE broker_order_submissions
    ADD COLUMN IF NOT EXISTS investment_id INTEGER;

CREATE INDEX IF NOT EXISTS ix_broker_order_submissions_investment_id
    ON broker_order_submissions (investment_id);

COMMIT;
