# Broker fill reconciliation migration: review and rollback

Migration: `backend/migrations/20261018_create_broker_reconciled_fills.sql`

## Apply
1. Confirm the Neon backup branch `backup-before-order-reconciliation` is visible and current.
2. Review the SQL file.
3. Apply it manually to the intended non-production/test database first.
4. Do not run it against production until separately approved.
5. The application route expects this table to exist; it does not create/alter it automatically.

## Rollback
Only roll back if reconciliation has not been used, or after explicitly preserving/exporting the imported fill and transaction records. Dropping this table removes the duplicate-prevention ledger, so a later reconciliation could re-import the same broker fills.

```sql
BEGIN;
DROP INDEX IF EXISTS ix_broker_reconciled_fills_exchange_order_id;
DROP INDEX IF EXISTS ix_broker_reconciled_fills_user_id;
DROP TABLE IF EXISTS broker_reconciled_fills;
COMMIT;
```

The rollback does not delete rows from `investment_transactions` or change `investments`; those are separate ledger changes and must not be automatically reversed without an audited reconciliation plan.
