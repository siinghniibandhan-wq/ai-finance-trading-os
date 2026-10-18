# Broker reconciliation migrations: review and rollback

These migrations are intentionally manual. They have **not** been applied to production.

## Migration order

Apply only to a disposable test database first, then to an explicitly approved staging database:

1. `backend/migrations/20261018_add_broker_submission_investment_id.sql`
2. `backend/migrations/20261018_create_broker_reconciled_fills.sql`
3. `backend/migrations/20261018_create_broker_trading_control.sql`

Before any non-test application:
- Verify the intended database and current schema.
- Confirm a current Neon backup/restore point and test the restore procedure.
- Confirm the existing `broker_order_submissions` table and its unique key are present.
- Record pre-migration schema and row counts.
- Run migrations one at a time with SQL error-stop enabled; stop on any unexpected result.
- Keep `MSTOCK_ORDER_ID_MAPPING_VERIFIED` unset or `0`. A schema migration is not approval to import fills or enable live trading.

## What each migration changes

- `add_broker_submission_investment_id.sql`: adds nullable investment/order metadata columns and an index. Existing submissions remain unlinked; reconciliation must not infer their investment.
- `create_broker_reconciled_fills.sql`: creates the durable fill de-duplication table and indexes.
- `create_broker_trading_control.sql`: creates the singleton trading control table. Missing row means OFF; the database default is OFF.

The reconciliation route expects these objects to exist. It does not apply migrations automatically.

## Rollback cautions

Rollback is not a routine step. Stop reconciliation first. If any fill has been imported, preserve and audit the fill markers, linked investment transactions, and investment quantities before changing schema. Dropping the deduplication table can permit the same broker fills to be imported again. Never automatically delete ledger transactions or reverse holding quantities as part of a schema rollback.

Only when reconciliation has never been used and after confirming backup/approval, the new objects can be removed with:

```sql
BEGIN;
DROP INDEX IF EXISTS ix_broker_reconciled_fills_exchange_order_id;
DROP INDEX IF EXISTS ix_broker_reconciled_fills_user_id;
DROP TABLE IF EXISTS broker_reconciled_fills;
DROP TABLE IF EXISTS broker_trading_control;
ALTER TABLE broker_order_submissions
    DROP COLUMN IF EXISTS investment_id,
    DROP COLUMN IF EXISTS symbol,
    DROP COLUMN IF EXISTS exchange,
    DROP COLUMN IF EXISTS side,
    DROP COLUMN IF EXISTS quantity;
COMMIT;
```

This removes the new schema only. It does not delete rows from `investment_transactions` or change `investments`; those are separate ledger changes and require a separately audited plan.

## Production boundary

No production SQL has been run. Do not merge/deploy, apply production migrations, enable live trading, or enable reconciliation imports until CI is green on the final head, the actual gateway ID mapping is verified from redacted read-only evidence, and the production schema/backup/rollback plan is approved.
