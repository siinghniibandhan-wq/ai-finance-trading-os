# Financial OS — Completion Tracker

**Working branch:** `feature/financial-os-completion-audit`  
**Baseline:** `main` at `cf6d9b4bef48cc7e2711510416d4e08a92b7027b`  
**Audit started:** 13 November 2026  
**Rule:** source implementation, automated tests, deployment, and production verification are separate states.

## Safety boundaries

- Preserve existing screens, forms, API contracts, state, and business workflows.
- No production deployment, AWS resource/configuration change, database migration/application, credential rotation, or live broker order without separate explicit approval.
- Never fabricate market ticks, OI, prices, tax inputs, or financial records.
- Keep broker live-order kill switch OFF unless separately approved.
- All m.Stock credentials and tokens remain server-side.

## Workstreams

| Workstream | Baseline finding | Status | Acceptance evidence |
|---|---|---|---|
| m.Stock live connection | REST checks previously returned HTTP 200. WebSocket handshake from recorded Sydney EC2 returned 502; latest user-run handshake returned 504 from `awselb/2.0`. Failure is before LOGIN/subscription. | Blocked by provider/connection path | Successful handshake from approved host; documented LOGIN success; subscription acknowledgements; timestamped ticks; heartbeat and reconnect tests. |
| Order Flow live data | UI and authenticated snapshot API/adapter exist. External derivatives gateway worker, WebSocket packet decoder, credential/session lifecycle and deployment are not in this repo. | Partial / blocked | Gateway contract implemented and tested; verified provider packet mapping; real fresh ticks; correct futures/options aggregation; stale/disconnected UI state. |
| Application-wide functional audit | Product modules are present, but no current end-to-end acceptance matrix was found. | In progress | Per-module API/UI/test review, regression tests, findings with severity and reproducible evidence. |
| Finance workflows | Finance modules exist; correctness and cross-module ledger consistency require systematic verification. | Not yet audited | Tests for account ownership, balances, transfers, receivables/payables, budgets, goals, bills, loans, and ledger reconciliation. |
| Investment workflows | Transaction ledger, holdings, weighted-average P&L and FIFO tax engine exist. Broker reconciliation and cash-account side effects need end-to-end validation. | Not yet audited | BUY/SELL/void/reversal/reconciliation tests, quantity and cash invariants, price freshness and tax-lot reconciliation. |
| Indian tax workflows | Multiple tax engines exist. Final liability currently has an explicit FY rule registry for FY 2026-27; other years fail closed. | Not yet audited | Rule-by-rule CA review, source evidence, regime/age/residency cases, capital-gain eligibility, loss set-off, TDS/advance-tax and ITR reconciliation. |
| AWS and deployment | Recorded EC2/service details are historical. Active frontend host, database host, IAM, network, secrets, backups, monitoring and deployment target are not verified from source. | Requires live read-only audit | Dated inventory from AWS/hosting accounts, deployment mapping, service health, backup/restore evidence and rollback procedure. |
| Database governance | SQL migration files and startup `create_all`/conditional ALTER logic exist. No unified migration runner/ledger is documented in the repo. | Design and implementation required | Unique migration IDs, checksums, ledger, locking, dry-run/status, verified backup gate, failure handling and staging tests. |
| Security | Existing auth, password hashing, route-level private-router inclusion, security headers and process-local rate limits exist. MFA, verification, reset, distributed throttling and CSP need review. | Not yet audited | Threat-model findings, automated tests, config verification and safe remediation PRs. |

## Immediate m.Stock incident record

Latest user-provided test:
- Endpoint: `wss://ws.mstock.trade`
- Result: `504 Gateway Time-out`
- Server header: `awselb/2.0`
- Timestamp: `Fri, 13 Nov 2026 13:34:25 GMT`
- Failure point: HTTP WebSocket upgrade; no LOGIN or subscription sent.

This does not prove invalid credentials, a bad subscription payload, or a frontend issue. Provider support has already been contacted by the user. Next technical evidence should be an India-origin handshake comparison and m.Stock's listener/upstream/target health investigation for the timestamp. Do not keep retrying in a tight loop.

## Confirmed code observations for audit

1. `frontend/src/order-flow/README.md` explicitly says the external gateway worker and provider binary decoder are not included.
2. `backend/app/services/order_flow_feed.py` consumes a normalized `GET /order-flow/snapshot` gateway response and validates the payload; it is an adapter, not the WebSocket client.
3. `backend/app/main.py` runs `Base.metadata.create_all()` and several conditional schema alterations for non-Vercel startup. This is not a controlled migration system.
4. `backend/app/routes/investment_transactions.py` creates/alters its table during request handling. This needs migration-governance review; do not remove it until a compatible migration path is prepared and tested.
5. `backend/app/routes/holdings.py` documents weighted-average portfolio P&L and explicitly says FIFO/LIFO are not implemented there. Tax capital-gains calculation is a separate FIFO engine; the two outputs must be clearly distinguished and reconciled.
6. `backend/app/routes/final_tax_liability.py` uses a year-specific rule registry and currently defines FY 2026-27 only. Unsupported years must continue to fail closed until reviewed rules are added.
7. `backend/app/main.py` applies authenticated-user dependency when registering private routers. Preserve that central boundary and test every route, including any newly added endpoint.
8. `backend/app/routes/auth.py` uses process-local login throttling; multi-worker/global enforcement still needs an external shared control.

## Execution sequence

1. Complete read-only source audit and build a reproducible module acceptance matrix.
2. Continue m.Stock provider diagnostics without changing production services or credentials.
3. Implement and test the derivatives gateway worker only after the provider protocol, sample packets and field/scaling specification are verified.
4. Complete finance, investment and tax regression audits; fix issues in isolated pull requests.
5. Perform read-only AWS and hosting inventory; propose changes separately.
6. Design and test migration governance on a disposable/staging database before any production use.
7. Run full CI and document exact commit/test/deployment evidence.

## Change log

- 2026-11-13: Created this tracker on the dedicated audit branch. No production resources, database schema, broker settings or live orders were changed.
