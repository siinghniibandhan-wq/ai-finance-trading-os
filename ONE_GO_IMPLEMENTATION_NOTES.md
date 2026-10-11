# Financial OS — One-go implementation notes

This update preserves the existing UI and tax module while adding the agreed account/transaction/investment architecture.

## Implemented in this source package

- Money account types expanded to bank, cash-in-hand, petty cash, wallet, credit card, credit line, loan, receivable, payable, investment/broker cash, and other.
- Transactions page has Income, Expense, and Transfer tabs. Existing detailed types remain visible under the three main tabs.
- Transfers are one financial transaction with source and destination account IDs. Both balances update in one database transaction; transfer records are excluded from income/expense calculations. Liability account transfers adjust outstanding liabilities in the appropriate direction.
- Account deletion is now deactivation, not physical deletion, preserving linked history.
- Finance Diary is an independent, user-ID-scoped, read-only API/page under Settings. It has no foreign keys to business records and no edit/delete endpoints. Account and transaction events preserve snapshots so history survives deletion.
- Investment account cash is represented by an `investment` account in Money → Accounts. Transfers can fund it. Investment buys require a matching broker cash account and sufficient funds; buys deduct cash and sells credit net proceeds.
- Investment records now store asset class, product type, instrument identity, broker cash account ID, and canonical instrument-master ID. A background `/api/instrument-master/` endpoint manages canonical instrument identities without adding a new UI tab.
- Investment trade creation, edits where supported, and voids write Finance Diary entries. Void remains an audit-preserving action.
- Added a regression test for transfer balance changes and Finance Diary preservation.

## Verification

- Python compilation: passed.
- Backend tests: 53 passed, 6 warnings.
- JSX/JavaScript syntax transpilation check: passed using the locally available TypeScript parser.
- Full Vite production build was not run because frontend dependencies (`vite`, React packages) are not installed in this runtime and dependency installation timed out.

## Important deployment note

The backend performs additive column migrations for the new transfer, investment, and instrument metadata fields. Deploy the backend changes together with the frontend package. Existing investment purchases that do not have a matching `investment` account for the same broker must first have that broker cash account created and funded before new trades can be recorded. Existing historical records are not auto-merged or rewritten.
