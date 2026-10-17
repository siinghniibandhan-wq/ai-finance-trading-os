# m.Stock gateway patch required for owner-only live trading toggle

**Status: patch instructions only; this file does not change the EC2 gateway.** The gateway source is deployed separately at `/home/ssm-user/mstock-gateway/app.py`.

## Required code changes in `app.py`

1. Add `import threading` if not already imported.
2. Add the following state near the existing `trading_enabled()` helper. This deliberately starts OFF on every process restart, regardless of a stale environment variable:

```python
import hmac
import threading

_TRADING_STATE_LOCK = threading.Lock()
_TRADING_ENABLED = False  # fail closed after every gateway restart

def trading_enabled():
    with _TRADING_STATE_LOCK:
        return _TRADING_ENABLED
```

3. Add this route next to the existing `/trading-status` route. Keep the existing `max_order_value()` and `max_order_qty()` helpers unchanged. The endpoint accepts a secret only from the backend; keep port 8000 bound to loopback and closed publicly.

```python
@app.post("/trading-toggle")
def set_trading_toggle():
    global _TRADING_ENABLED
    expected = os.environ.get("MSTOCK_GATEWAY_SECRET", "").strip()
    supplied = request.headers.get("X-Financial-OS-Gateway-Secret", "")
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify({"detail": "Unauthorized"}), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or type(payload.get("enabled")) is not bool:
        return jsonify({"detail": "enabled must be a boolean"}), 400

    with _TRADING_STATE_LOCK:
        _TRADING_ENABLED = payload["enabled"]

    return jsonify({
        "trading_enabled": _TRADING_ENABLED,
        "max_order_value": max_order_value(),
        "max_order_qty": max_order_qty(),
    }), 200
```

This uses Flask's existing `request` and `jsonify`; add imports only if missing. Ensure the existing `/trading-status` response calls `trading_enabled()`, and that `order_precheck()` calls the same helper before every POST/PUT/DELETE order operation. The toggle does not bypass token validity, broker order validation, or the existing order value/quantity limits.

## Secret and safety

- Set the same random `MSTOCK_GATEWAY_SECRET` value in the backend and gateway environments, without printing it in shell output or logs.
- Do not expose port 8000 publicly. Do not put the secret in frontend environment variables or JavaScript.
- The backend rejects non-loopback gateway URLs for this control.
- No live order should be placed to test this. Verify by reading status, switching OFF, reading status, switching ON only after an explicit real-money confirmation, and switching OFF again.
- This patch has not been applied, syntax-checked, or tested against the live gateway.
