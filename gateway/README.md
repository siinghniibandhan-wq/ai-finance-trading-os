# m.Stock read-only market stream gateway patch

## Scope
- Maintains a single read-only Type A WebSocket worker.
- Waits for a successful text LOGIN acknowledgement before sending the subscription JSON.
- Treats LOGIN errors, unknown/binary pre-login frames and acknowledgement timeouts as connection failures; no subscription is sent in those cases.
- Reconnects after access-token changes or derivative-token-set changes, then authenticates and subscribes again.
- Keeps a bounded in-memory latest-tick cache. No order placement, database writes, or trading limits are changed.

## Gateway integration
The uploaded Flask gateway already defines authenticated routes:
- POST /market-stream/start: {"tokens":[...],"mode":3}; maximum 200 positive tokens.
- POST /market-stream/stop
- GET /market-stream/status
- GET /market-stream/snapshot

Install `market_stream.py` and `mstock_stream.py` beside the gateway's existing `app.py`. Keep the existing route definitions and existing `ACCESS_TOKEN`, token validation, SSM API-key parameter and `FINANCIAL_OS_GATEWAY_SECRET` wiring. Do not replace the production `app.py` with the reconstructed upload.

## Verification
Run from this directory:
```bash
python -m pytest -q
python -m py_compile market_stream.py mstock_stream.py
```

## Deployment boundary
This patch is not deployed. Reconcile it with the exact current EC2 gateway files, back up the current files, deploy only after explicit production approval, then verify LOGIN acknowledgement, subscription token list, fresh ticks and the authenticated snapshot endpoint. The actual provider LOGIN acknowledgement payload must be confirmed against a real m.Stock session before declaring the stream live.
