# m.Stock gateway reconciliation patch

This patch is for the separate Flask gateway at `/home/ssm-user/mstock-gateway/app.py`.
It is **not** automatically deployed when the Financial OS backend PR is merged.

## Required configuration

Create the AWS Systems Manager SecureString parameter `/financial-os/mstock/gateway-secret` with a long random secret. Configure the Financial OS backend environment with the same value as `MSTOCK_GATEWAY_SECRET`. Do not put the value in source control or paste it into chat. **The backend refuses to send this secret to an `http://` gateway URL. Configure HTTPS or a private encrypted tunnel first; the current public-IP HTTP URL must not be used with the shared secret.**

The gateway's EC2 role must be allowed to read that parameter. The routes below fail closed if the parameter is unavailable.

## Gateway code

Add the following block after the existing order routes and before `if __name__ == "__main__":`. It reuses the gateway's existing `ACCESS_TOKEN`, `token_is_valid()`, `get_parameter()`, `MSTOCK_API_BASE`, `order_headers()`, `ORDER_LOG`, `log_order()`, and Flask `app`.

```python
import hmac

MSTOCK_ORDER_BOOK_URL = f"{MSTOCK_API_BASE}/openapi/typea/orders"
MSTOCK_TRADE_BOOK_URL = f"{MSTOCK_API_BASE}/openapi/typea/tradebook"
GATEWAY_SECRET_PARAMETER = "/financial-os/mstock/gateway-secret"


def _require_financial_os_gateway_secret():
    expected = get_parameter(GATEWAY_SECRET_PARAMETER)
    supplied = request.headers.get("X-Financial-OS-Gateway-Secret", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return None


def _response_order_id(body):
    if not isinstance(body, dict):
        return None
    for key in ("order_id", "orderid", "orderId", "nOrdNo"):
        value = body.get(key)
        if value:
            return str(value)
    for key in ("data", "result", "order"):
        nested = body.get(key)
        found = _response_order_id(nested)
        if found:
            return found
    return None


def _client_reference_by_order_id():
    mapping = {}
    try:
        with open(ORDER_LOG, "r") as log_file:
            for line in log_file:
                try:
                    event = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if event.get("event") != "place_response":
                    continue
                client_id = event.get("client_id")
                order_id = _response_order_id(event.get("body"))
                if client_id and order_id:
                    mapping[order_id] = str(client_id)
    except FileNotFoundError:
        pass
    return mapping


def _extract_rows(payload, accepted_keys):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in accepted_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for key in ("data", "result"):
            value = payload.get(key)
            if isinstance(value, dict):
                rows = _extract_rows(value, accepted_keys)
                if rows is not None:
                    return rows
    return None


@app.get("/orders")
def list_orders():
    blocked = _require_financial_os_gateway_secret()
    if blocked:
        return blocked
    if not token_is_valid():
        return jsonify({"status": "error", "message": "m.Stock authentication required",
                        "code": "AUTH_REQUIRED"}), 401
    try:
        response = requests.get(MSTOCK_ORDER_BOOK_URL, headers=order_headers(), timeout=20)
        try:
            body = response.json()
        except ValueError:
            return jsonify({"status": "error", "message": "m.Stock returned non-JSON order data"}), 502
        if response.status_code == 401:
            return jsonify({"status": "error", "message": "m.Stock access token expired",
                            "code": "AUTH_REQUIRED"}), 401
        if response.status_code != 200:
            return jsonify({"status": "error", "message": "m.Stock order-book request failed"}), 502

        # The backend must be able to filter this shared broker account's order
        # book by Financial OS user. Enrich only orders whose broker order ID
        # matches a locally logged placement; never expose unmapped rows as if
        # they belonged to a particular user.
        rows = _extract_rows(body, ("orders", "orderbook", "order_book", "items", "data"))
        if rows is None:
            return jsonify({"status": "error", "message": "Unsupported m.Stock order-book response shape"}), 502
        references = _client_reference_by_order_id()
        enriched = []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            row = dict(raw)
            order_id = next((str(row[key]) for key in
                             ("order_id", "orderid", "orderId", "nOrdNo")
                             if row.get(key) not in (None, "")), None)
            if order_id and order_id in references:
                row["client_reference"] = references[order_id]
            enriched.append(row)
        return jsonify({"status": "success", "orders": enriched})
    except requests.RequestException:
        return jsonify({"status": "error", "message": "Unable to reach m.Stock"}), 502


@app.get("/trades")
def list_trades():
    blocked = _require_financial_os_gateway_secret()
    if blocked:
        return blocked
    if not token_is_valid():
        return jsonify({"status": "error", "message": "m.Stock authentication required",
                        "code": "AUTH_REQUIRED"}), 401
    try:
        response = requests.get(MSTOCK_TRADE_BOOK_URL, headers=order_headers(), timeout=30)
        try:
            body = response.json()
        except ValueError:
            return jsonify({"status": "error", "message": "m.Stock returned non-JSON trade data"}), 502
        if response.status_code == 401:
            return jsonify({"status": "error", "message": "m.Stock access token expired",
                            "code": "AUTH_REQUIRED"}), 401
        if response.status_code != 200:
            return jsonify({"status": "error", "message": "m.Stock trade-book request failed"}), 502

        rows = _extract_rows(body, ("trades", "tradebook", "items", "data"))
        if rows is None:
            return jsonify({"status": "error", "message": "Unsupported m.Stock trade-book response shape"}), 502

        references = _client_reference_by_order_id()
        enriched = []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            row = dict(raw)
            order_id = next((str(row[key]) for key in
                             ("order_id", "orderid", "orderId", "nOrdNo")
                             if row.get(key) not in (None, "")), None)
            # Trade-book rows are executions. Only enrich with our own client
            # reference when the order ID was returned by our logged placement.
            if order_id and order_id in references:
                row["client_reference"] = references[order_id]
            enriched.append(row)
        return jsonify({"status": "success", "trades": enriched})
    except requests.RequestException:
        return jsonify({"status": "error", "message": "Unable to reach m.Stock"}), 502
```

## Important limitations and rollout

- After adding the helper, also add these three lines at the very start of each existing `place_order()`, `modify_order()`, and `cancel_order()` route, before any order processing:
  ```python
  blocked = _require_financial_os_gateway_secret()
  if blocked:
      return blocked
  ```
  This protects order placement, modification, and cancellation with the same secret as the read-only endpoints. Keep the existing trading switch and order caps unchanged.
- The existing gateway logs `client_id` and broker placement responses. This patch maps executed trade rows to the Financial OS reference using the broker order ID; it does not assume the broker echoes custom client references.
- The log file must persist across service restarts and remain readable by the gateway process. Back up the log before changes.
- Before enabling reconciliation, verify the exact field names in a **read-only** response from your m.Stock trade book. The backend skips rows it cannot normalize and never treats order-book acknowledgements as fills.
- Add the shared secret to both AWS Parameter Store and the backend environment before calling the new endpoints. Configure `MSTOCK_GATEWAY_URL` to an HTTPS URL before setting `MSTOCK_GATEWAY_SECRET`; the backend deliberately fails closed if the URL is HTTP. Restart only during a planned maintenance window.
- Test `GET /trades` and `GET /orders` with an invalid secret (expect 401), then with a valid secret and an authenticated m.Stock session. Do not test by submitting a real order.
- This patch does not change the existing order-placement trading switch or its caps. Do not enable live trading as part of reconciliation testing.
