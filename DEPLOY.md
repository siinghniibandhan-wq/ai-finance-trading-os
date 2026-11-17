# Market Flow gateway deployment — approval required before restart

This document covers the gateway-only portion of Market Flow. The application changes in this branch use the existing Financial OS Bearer session and existing Markets REST integration. They do not require changing login/session code or the Markets tab.

## Scope and protected files

Gateway files to add/replace:
- `market_stream.py` — replace the existing worker.
- `order_flow_snapshot.py` — add the read-only normalized snapshot adapter.
- `app.py` — add only the blueprint registration shown below.

Must remain untouched:
- `/auth`, `/order`, `orders_patch.py`, `mstock_stream.py`.
- Existing Markets REST routes and gateway behaviour.
- All credentials and secret values.

The gateway process is a single process at `/home/ssm-user/mstock-gateway`, bound to `127.0.0.1:8000`. Confirm the actual unit and working directory on the host before running commands.

## 1. Backup (read-only to live service)

Run on EC2:

```bash
cd /home/ssm-user/mstock-gateway
stamp=$(date -u +%Y%m%dT%H%M%SZ)
cp -a market_stream.py "market_stream.py.bak-$stamp"
cp -a app.py "app.py.bak-$stamp"
test ! -e order_flow_snapshot.py || cp -a order_flow_snapshot.py "order_flow_snapshot.py.bak-$stamp"
```

Record the backup names. Do not print environment variables or credentials.

## 2. Copy patch files and register the blueprint

Copy the reviewed `market_stream.py` and new `order_flow_snapshot.py` into this directory. Do not overwrite any other gateway file.

In `app.py`, place the following immediately after the existing `app.register_blueprint(_market_stream_blueprint)` registration. Reuse the existing functions/constants already defined by the gateway; do not duplicate or alter its auth flow.

```python
from order_flow_snapshot import create_order_flow_blueprint

def _scriptmaster_text():
    api_key = get_parameter("/financial-os/mstock/api-key")
    response = requests.get(
        MSTOCK_SCRIPTMASTER_URL,
        headers={
            "X-Mirae-Version": "1",
            "Authorization": f"token {api_key}:{ACCESS_TOKEN}",
        },
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError("m.Stock instrument master request failed")
    return response.text

app.register_blueprint(create_order_flow_blueprint(
    worker=_market_stream_blueprint.market_stream_worker,
    token_valid=token_is_valid,
    scriptmaster_loader=_scriptmaster_text,
    gateway_secret_ok=_gateway_secret_ok,
))
```

Before saving, verify that `get_parameter`, `requests`, `MSTOCK_SCRIPTMASTER_URL`, `ACCESS_TOKEN`, `token_is_valid`, `_gateway_secret_ok`, and `_market_stream_blueprint.market_stream_worker` are the existing gateway names. If any differ, stop and reconcile the snippet; do not alter `/auth` or token storage.

## 3. Syntax and diff checks (no restart)

```bash
cd /home/ssm-user/mstock-gateway
python3 -m py_compile market_stream.py order_flow_snapshot.py app.py
git diff --check
git diff -- app.py market_stream.py order_flow_snapshot.py
```

Inspect the diff. It must contain only the two intended file changes and the single blueprint registration. Do not display secrets or environment values. This step does not restart the process.

## 4. Restart — explicit approval required

**Do not run this step until the owner explicitly approves it.**

```bash
sudo systemctl restart mstock-gateway
sudo systemctl --no-pager --full status mstock-gateway
```

A restart destroys the gateway's in-memory m.Stock access token. A fresh TOTP login through the existing `POST /auth` flow is required afterwards. Until that login succeeds, the derivatives worker must remain `auth_required`; the Markets tab may also be unavailable because the gateway token is no longer in memory. Do not alter the Financial OS login/session to work around this.

## 5. Live verification — after approved restart and fresh TOTP login

Use the gateway secret from the existing secure operator environment. Never paste it into chat, shell history, screenshots, or logs. Example commands read the secret from an already-exported shell variable without printing it:

```bash
: "${FINANCIAL_OS_GATEWAY_SECRET:?Set the gateway secret securely in this shell first}"
curl --fail --silent --show-error \
  -H "X-Financial-OS-Gateway-Secret: ${FINANCIAL_OS_GATEWAY_SECRET}" \
  http://127.0.0.1:8000/order-flow/status

curl --fail --silent --show-error \
  -H "X-Financial-OS-Gateway-Secret: ${FINANCIAL_OS_GATEWAY_SECRET}" \
  http://127.0.0.1:8000/order-flow/snapshot
```

The first snapshot request starts the worker asynchronously. Repeat status/snapshot after a short interval. Share only these redacted fields for protocol diagnosis:
- `stream.login_state`
- `stream.login_confirmed_by`
- `stream.last_login_response` (redact tokens, API keys, account details)
- `stream.last_error` (redact any credential-like content)
- `coverage` (instrument tokens may also be redacted if preferred)

Do not enable strict LOGIN-ack mode or change the WebSocket `mode` message until actual EC2 output is reviewed. The current matcher and mode are provisional because the live EC2 WebSocket handshake has not yet been verified.

## Rollback

Only after approval to operate on the gateway:

```bash
cd /home/ssm-user/mstock-gateway
cp -a market_stream.py.bak-<timestamp> market_stream.py
cp -a app.py.bak-<timestamp> app.py
# Remove order_flow_snapshot.py only if it did not exist before this deployment.
python3 -m py_compile market_stream.py app.py
```

A rollback restart also clears the in-memory m.Stock token and requires a fresh TOTP login. Obtain approval before restarting.

## Verification boundary

Unit and mocked integration tests do not prove the EC2-to-m.Stock WebSocket handshake, LOGIN acceptance, subscription delivery, binary tick decoding against current live packets, or live Market Flow display. Those require the owner-approved restart, fresh TOTP login, and the live checks in step 5.
