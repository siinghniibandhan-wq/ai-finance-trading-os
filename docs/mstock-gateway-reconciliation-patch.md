# m.Stock gateway reconciliation patch (review only)

Target: `/home/ssm-user/mstock-gateway/app.py`

This is an insertion patch for the five-part source provided in this conversation. Insert the code below immediately before the existing `if __name__ == "__main__":` block. It does not replace existing routes, does not submit/modify/cancel orders, and does not require a restart until the owner explicitly applies and approves it.

**Upstream paths are configurable** because they must be checked against the account's currently documented m.Stock Type A API before application:
- `MSTOCK_ORDER_BOOK_URL` defaults to `/openapi/typea/orders`
- `MSTOCK_TRADE_BOOK_URL` defaults to `/openapi/typea/tradebook`
- `MSTOCK_TRADE_HISTORY_URL` defaults to `/openapi/typea/trades`

```python
# ============================================================
# READ-ONLY BROKER BOOKS FOR FINANCIAL OS RECONCILIATION
# ============================================================

MSTOCK_ORDER_BOOK_URL = os.environ.get(
    "MSTOCK_ORDER_BOOK_URL", f"{MSTOCK_API_BASE}/openapi/typea/orders"
)
MSTOCK_TRADE_BOOK_URL = os.environ.get(
    "MSTOCK_TRADE_BOOK_URL", f"{MSTOCK_API_BASE}/openapi/typea/tradebook"
)
MSTOCK_TRADE_HISTORY_URL = os.environ.get(
    "MSTOCK_TRADE_HISTORY_URL", f"{MSTOCK_API_BASE}/openapi/typea/trades"
)


def read_only_precheck():
    if not _gateway_secret_ok():
        return jsonify({"status": "error", "message": "Gateway secret invalid",
                        "code": "GATEWAY_SECRET_INVALID"}), 403
    if not token_is_valid():
        return jsonify({"status": "error", "message": "m.Stock authentication required",
                        "code": "AUTH_REQUIRED"}), 401
    return None


def _mstock_get_json(url, params=None):
    response = requests.get(url, headers=order_headers(), params=params, timeout=20)
    try:
        body = response.json()
    except ValueError as exc:
        raise RuntimeError("m.Stock returned a non-JSON broker-book response") from exc
    if response.status_code == 401:
        raise PermissionError("m.Stock access token expired or invalid")
    if response.status_code != 200:
        raise RuntimeError(str(body.get("message", "m.Stock broker-book request failed"))[:200])
    # Some provider errors use HTTP 200, so inspect the JSON status too.
    if isinstance(body, dict) and str(body.get("status", "")).lower() in {"error", "failed", "failure"}:
        raise RuntimeError(str(body.get("message", "m.Stock broker-book request failed"))[:200])
    return body


def _list_from_book(body, keys):
    if isinstance(body, list):
        return body
    if not isinstance(body, dict):
        return None
    for key in keys:
        if isinstance(body.get(key), list):
            return body[key]
    data = body.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return data[key]
    return None


def _book_value(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _local_order_references():
    # Map response order IDs to client_id from the gateway's existing order log.
    # Do not use tags or symbol/price/quantity/time heuristics.
    by_order_id, requests_by_client = {}, {}
    try:
        with open(ORDER_LOG, "r", encoding="utf-8") as stream:
            for line in stream:
                try:
                    item = json.loads(line)
                except (ValueError, TypeError):
                    continue
                event = item.get("event")
                if event == "place_request":
                    client_id = _book_value(item, "client_id")
                    if client_id:
                        requests_by_client[client_id] = item
                elif event == "place_response":
                    client_id, body = _book_value(item, "client_id"), item.get("body")
                    if not client_id or not isinstance(body, dict):
                        continue
                    nested = body.get("data") if isinstance(body.get("data"), dict) else {}
                    for key in ("order_id", "orderid", "exchange_order_id", "exchangeorderid"):
                        order_id = _book_value(body, key) or _book_value(nested, key)
                        if order_id:
                            by_order_id[order_id] = client_id
    except OSError:
        pass
    return by_order_id, requests_by_client


def _enrich_trade_rows(rows, order_rows):
    by_logged_id, requests_by_client = _local_order_references()
    by_exchange_order_id = {}
    for order in order_rows:
        if not isinstance(order, dict):
            continue
        exch_id = _book_value(order, "exchange_order_id", "EXCH_ORDER_NUMBER", "exchangeorderid")
        order_id = _book_value(order, "order_id", "orderid", "ORDER_NUMBER")
        client_id = by_logged_id.get(order_id) or by_logged_id.get(exch_id)
        if not exch_id or not client_id:
            continue
        original_request = requests_by_client.get(client_id, {})
        by_exchange_order_id[exch_id] = {
            "client_reference": client_id,
            "exchange": _book_value(order, "exchange", "EXCHANGE") or _book_value(original_request, "exchange"),
            "symbol": _book_value(order, "tradingsymbol", "symbol", "SYMBOL") or _book_value(original_request, "tradingsymbol"),
        }

    enriched = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        exch_id = _book_value(row, "exchange_order_id", "EXCH_ORDER_NUMBER", "exchangeorderid")
        matched = by_exchange_order_id.get(exch_id)
        # No match = no ownership attribution. Never infer from a symbol or tag.
        if not exch_id or not matched:
            continue
        item = dict(row)
        item["exchange_order_id"] = exch_id
        item["client_reference"] = matched["client_reference"]
        # Prefer the tradebook's SYMBOL code. /trades tradingsymbol may be a company name.
        item["symbol"] = _book_value(row, "SYMBOL", "symbol") or matched["symbol"]
        item["exchange"] = _book_value(row, "EXCHANGE", "exchange") or matched["exchange"]
        item["trade_id"] = _book_value(row, "TRADE_NUMBER", "trade_id", "tradeid", "fill_id")
        item["side"] = _book_value(row, "BUY_SELL", "side", "transaction_type")
        item["quantity"] = _book_value(row, "QUANTITY", "quantity", "traded_quantity")
        item["price"] = _book_value(row, "PRICE", "price", "trade_price", "average_price")
        item["trade_date"] = _book_value(row, "TRADE_DATE", "ORDER_DATE_TIME", "trade_date", "date")
        if item["trade_id"]:
            enriched.append(item)
    return enriched


def _read_trade_rows(url, keys, params=None):
    try:
        body = _mstock_get_json(url, params=params)
        rows = _list_from_book(body, keys)
        if rows is None:
            return jsonify({"status": "error", "message": "Unsupported m.Stock broker-book response shape"}), 502
        order_body = _mstock_get_json(MSTOCK_ORDER_BOOK_URL)
        order_rows = _list_from_book(order_body, ("orders", "orderbook", "order_book", "data"))
        if order_rows is None:
            return jsonify({"status": "error", "message": "Unsupported m.Stock order-book response shape"}), 502
        return jsonify({"status": "success", "data": _enrich_trade_rows(rows, order_rows)})
    except PermissionError:
        return jsonify({"status": "error", "message": "m.Stock access token expired or invalid",
                        "code": "AUTH_REQUIRED"}), 401
    except requests.RequestException:
        return jsonify({"status": "error", "message": "Unable to reach m.Stock broker-book API"}), 502
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)[:200]}), 502


@app.get("/orderbook")
def read_orderbook():
    blocked = read_only_precheck()
    if blocked:
        return blocked
    try:
        body = _mstock_get_json(MSTOCK_ORDER_BOOK_URL)
        rows = _list_from_book(body, ("orders", "orderbook", "order_book", "data"))
        if rows is None:
            return jsonify({"status": "error", "message": "Unsupported m.Stock order-book response shape"}), 502
        return jsonify({"status": "success", "data": rows})
    except PermissionError:
        return jsonify({"status": "error", "message": "m.Stock access token expired or invalid",
                        "code": "AUTH_REQUIRED"}), 401
    except requests.RequestException:
        return jsonify({"status": "error", "message": "Unable to reach m.Stock order-book API"}), 502
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)[:200]}), 502


@app.get("/tradebook")
def read_tradebook():
    blocked = read_only_precheck()
    if blocked:
        return blocked
    return _read_trade_rows(MSTOCK_TRADE_BOOK_URL, ("tradebook", "trades", "items", "data"))


@app.get("/tradehistory")
def read_tradehistory():
    blocked = read_only_precheck()
    if blocked:
        return blocked
    from_date = request.args.get("fromdate", "").strip()
    to_date = request.args.get("todate", "").strip()
    if not from_date or not to_date:
        return jsonify({"status": "error", "message": "fromdate and todate are required (YYYY-MM-DD)"}), 400
    try:
        time.strptime(from_date, "%Y-%m-%d")
        time.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"status": "error", "message": "fromdate and todate must use YYYY-MM-DD"}), 400
    return _read_trade_rows(MSTOCK_TRADE_HISTORY_URL, ("trades", "tradehistory", "items", "data"),
                            {"fromdate": from_date, "todate": to_date})
```

## Application caveats
- The existing shared-secret check is reused; trading-enabled is not required for read-only endpoints.
- Client attribution requires an exact `exchange_order_id` match and a corresponding order response recorded in `orders.log.jsonl`. If m.Stock omits these IDs, rows are deliberately omitted rather than guessed.
- Validate the upstream endpoint paths and response field names against the account's actual m.Stock API before applying.
- This patch has not been applied to AWS and must not be deployed without separate review.
