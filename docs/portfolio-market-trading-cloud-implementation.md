# Portfolio / Market Trading — Cloud Implementation Handoff

## Scope and safety constraints

Implement only Portfolio and Market trading flows. Do not change theme, CSS, styling, navigation, or unrelated modules. Preserve all existing m.Stock market-data routes and current auth.

Do not merge or deploy until focused tests pass and the production database/gateway configuration is verified. Never place real-money orders as tests.

## Source facts from the deployed gateway inspection

The gateway file is `/home/ssm-user/mstock-gateway/app.py`.

- `order_headers()` is at lines 900–905 and currently returns only `X-Mirae-Version` and m.Stock `Authorization`.
- `order_precheck()` begins at line 908 and currently checks `trading_enabled()` and `token_is_valid()`; the inspected code does not validate the Financial OS gateway shared secret.
- `POST /order` begins at line 931.
- `PUT /order/<order_id>` and `DELETE /order/<order_id>` exist in the supplied excerpt.
- Gateway duplicate suppression uses in-memory `_recent_orders` and `_order_lock`; this is not durable across a gateway process restart.
- Gateway order parsing expects fields such as `tradingsymbol`, `transaction_type`, `product`, and `ref_price`. The FastAPI broker route currently sends `symbol`, `side`, `product_type`, and `quote_price`.
- The supplied grep output did not find `GET /orders`. Add it only after confirming the broker's `ORDER_BASE` GET contract from the existing gateway implementation/provider documentation.

## Gateway code changes to apply

### 1. Add constant-time shared-secret validation

Add `import hmac` with the imports. Read a secret from the gateway process environment; never hard-code the value:

```python
FINANCIAL_OS_GATEWAY_SECRET = os.getenv("FINANCIAL_OS_GATEWAY_SECRET", "").strip()


def validate_financial_os_gateway_secret():
    configured = FINANCIAL_OS_GATEWAY_SECRET
    supplied = request.headers.get("X-Financial-OS-Gateway-Secret", "")
    if not configured or not supplied or not hmac.compare_digest(supplied, configured):
        return jsonify({
            "status": "error",
            "message": "Gateway authentication required",
            "code": "GATEWAY_AUTH_REQUIRED",
        }), 401
    return None
```

Call this check at the start of `order_precheck()`, before trading/token checks:

```python
def order_precheck():
    secret_block = validate_financial_os_gateway_secret()
    if secret_block:
        return secret_block
    if not trading_enabled():
        return jsonify({"status": "error", "message": "Trading is switched off",
                        "code": "TRADING_DISABLED"}), 403
    if not token_is_valid():
        return jsonify({"status": "error", "message": "m.Stock authentication required",
                        "code": "AUTH_REQUIRED"}), 401
    return None
```

Use the same randomly generated secret value for backend `MSTOCK_GATEWAY_SECRET` and gateway `FINANCIAL_OS_GATEWAY_SECRET`, stored in protected service environment/config—not in GitHub or logs. Keep the gateway bound to loopback/private access as appropriate for the deployed topology. Do not print secrets while verifying configuration.

### 2. Accept the backend's field names and map them to m.Stock fields

In `place_order()`, support both the existing gateway field names and the backend names, preserving legacy callers. Adapt the parsing currently beginning after `d = request.get_json(silent=True) or {}`:

```python
symbol = str(d.get("tradingsymbol", d.get("symbol", ""))).strip().upper()
side = str(d.get("transaction_type", d.get("side", ""))).strip().upper()
exchange = str(d.get("exchange", "NSE")).strip().upper()

product = str(d.get("product", "")).strip().upper()
if not product:
    requested_product = str(d.get("product_type", "")).strip().upper()
    product = {
        "DELIVERY": "CNC",
        "INTRADAY": "MIS",
    }.get(requested_product, requested_product)

order_type = str(d.get("order_type", "MARKET")).strip().upper()
validity = str(d.get("validity", "DAY")).strip().upper()
qty = int(d.get("quantity", 0))
price = float(d.get("price", 0) or 0)
trigger = float(d.get("trigger_price", 0) or 0)
ref_price = float(d.get("ref_price", d.get("quote_price", 0)) or 0)
client_id = str(d.get("client_id", "")).strip()
```

Keep the existing validation and risk caps after this parsing. Continue constructing the m.Stock form with `tradingsymbol`, `transaction_type`, `product`, and other provider field names. Do not weaken quantity/value limits. Invalid conversions should return HTTP 400 instead of an unhandled exception.

### 3. Make order-book access available to the backend

First verify from the existing gateway/provider contract that `GET ORDER_BASE` returns the configured account's order book. If verified, add a `GET /orders` route that validates the Financial OS shared secret and m.Stock token, then calls the existing `send_to_mstock("GET", ORDER_BASE, None)` and returns the provider response/status. The backend calls `GET /orders` and expects JSON. Do not invent a different provider URL or response contract.

### 4. Preserve ambiguous outcomes

The backend durable reservation in PR #86 must remain committed before gateway submission. Never automatically retry an order when the request timed out or the gateway response is ambiguous. Keep the reservation blocked until the broker order book is reconciled by a human/operator. The gateway's in-memory cache is only an additional short-window guard, not the source of durable idempotency.

## Backend and frontend integration

The current backend route is `backend/app/routes/broker_orders.py`. It:
- restricts order placement/order book to the configured platform admin;
- sends `X-Financial-OS-Gateway-Secret`;
- stores a persistent `BrokerOrderSubmission` reservation before sending;
- deliberately returns `portfolio_updated: false` until confirmed fills are reconciled.

The Market instrument view in `frontend/src/App.jsx` already has BUY/SELL buttons and submits `side`, `symbol`, `exchange`, `product_type`, `order_type`, `validity`, `quantity`, `price`, `quote_price`, and `client_id` to `/api/broker-orders/`. Keep the current UI and styles unchanged.

Use the existing gateway `PUT /order/<order_id>` and `DELETE /order/<order_id>` only after adding authenticated backend proxy routes and confirming the exact request/response contract. Expose modify/cancel buttons only where an order ID and current order status make the action valid. Do not route these actions to investment-record edit/delete APIs.

Do not update holdings based merely on accepted order requests. Implement holdings/ledger changes only from confirmed fills, with duplicate-fill protection and consistent reversal/edit/delete behavior. If the broker does not expose a reliable fill/trade endpoint in the existing contract, report that blocker instead of fabricating fills.

## Required verification before merge/deploy

1. Unit tests for gateway-secret missing/wrong/correct values (no real credentials).
2. Payload mapping tests: backend BUY/SELL fields map to `transaction_type`, `symbol` maps to `tradingsymbol`, DELIVERY→CNC and INTRADAY→MIS, `quote_price` maps to `ref_price`.
3. Duplicate client ID: second request is blocked; same ID with changed payload is rejected.
4. PostgreSQL concurrency test and new-session/restart test for durable backend reservation.
5. Gateway timeout/ambiguous response leaves reservation blocked; no automatic retry.
6. Order-book, modify and cancel tests using a mocked provider.
7. Market quote/search/history regression tests to confirm existing m.Stock market data remains unchanged.
8. Verify production PostgreSQL has `broker_order_submissions` and the backend DB role can create/read/write it.
9. Verify gateway and backend environment configuration without printing secret values.
10. Do not merge/deploy until these checks are green. No live order should be placed as a test.

## Current known verification boundary

GitHub CI for PR #86 head `97a24bea10f82036b3317410c72ce1d7c940106f` previously passed 16 broker-order tests, backend financial-integrity tests, and Market search/quote regression tests. Those are CI results only; they do not verify AWS runtime configuration or actual broker acceptance/fill reconciliation.
