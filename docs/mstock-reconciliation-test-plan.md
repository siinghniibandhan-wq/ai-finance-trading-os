# m.Stock fill reconciliation — test readiness checklist

## Safety defaults

- Keep `MSTOCK_ORDER_ID_MAPPING_VERIFIED=0` or unset.
- Do not apply the SQL migration to production for this test.
- Do not place, modify, or cancel broker orders.
- Do not enable import mode until a real successful placement-response ID is proven to join to the broker order book and the trade book. A matching symbol, price, quantity, or timestamp is not proof.

## 1. Run unit/regression tests

From the repository root:

```bash
cd backend
python -m pytest tests/test_broker_reconciliation.py -q
```

Then run the backend financial-integrity and broker-order API regression suites used by CI. Use the exact test paths configured in `.github/workflows`; do not skip failures.

The reconciliation tests cover documented trade-book fields, date formats, strict symbol/order matching, non-finite values, dry-run defaults, mapping-flag strictness, and top-level/nested gateway error envelopes.

## 2. Verify the gateway without changing it

Use only the read-only endpoints after the existing gateway has valid authentication:

- `GET /orders`
- `GET /tradebook`
- `GET /tradehistory?fromdate=YYYY-MM-DD&todate=YYYY-MM-DD`

Capture redacted samples of:
1. one existing `place_request` and its matching `place_response` log event;
2. the corresponding order-book row;
3. the corresponding executed trade-book row.

Redact API keys, access tokens, personal data, and unrelated orders. Verify the same placement-response `order_id` is present in the order book and can be joined to the trade row through the exact exchange-order identifier. If any link is absent or ambiguous, stop; the row must remain unmatched.

## 3. Exercise backend dry-run

With the mapping flag unset or set to `0`, call the admin-only `POST /api/broker-orders/reconcile` in a non-production test environment. Confirm:

- response status is `dry_run`;
- `imported_count` is `0`;
- no marker, investment transaction, or holding quantity is written;
- malformed/error gateway responses return a safe error and do not import fills.

## 4. Controlled import test — staging only

Do not perform this step until mapping is independently verified, the migration is applied to a disposable/staging database, and a backup/rollback path is confirmed. Use existing historical fill data only; do not create a live order to generate test data.

Verify a repeated reconciliation imports a fill once, duplicate fills are counted separately, partial fills cannot exceed the submitted quantity, mismatched ownership/symbol/exchange/side is skipped, a failed ledger write rolls back the marker and holding update, and historical execution price does not overwrite current market price.

## Current boundary

Repository code and regression tests are prepared for test execution. The live gateway response mapping has not been verified from real redacted samples, the gateway patch remains documentation-only, and production migrations remain unapplied. Therefore this is **ready for safe dry-run testing**, not yet cleared for live import.
