# Order Flow workspace

The Financial OS navigation exposes **Order Flow** separately from the existing **Markets** workspace. Existing Markets, portfolio and broker order workflows remain separate and unchanged.

## Phase 1 — interactive board

The workspace includes the responsive Flow Diagram, ranked bullish/bearish instruments, sector highlighting, linked chart/list focus, pinned instrument details, option OI profile, support/resistance, conviction checks, keyboard navigation and persistent universe/instrument preferences.

The source project's interaction/layout model has been adapted to Financial OS; this is not a verbatim component transplant.

## Phase 2 — implemented application-side work

- Pure backend transformations for futures contract-month aggregation, current OI change/percentage, and strike-wise CE/PE OI aggregation.
- Feed freshness classification: `fresh`, `stale`, `disconnected`.
- Authenticated, read-only API: `GET /api/order-flow/snapshot?symbol=NIFTY`.
- Server-side derivatives gateway adapter, using `MSTOCK_DERIVATIVES_GATEWAY_URL` and the existing gateway secret header.
- Frontend feed status panel with authenticated polling, freshness display and bounded exponential retry (10–60 seconds).
- Backend tests for aggregation, freshness, gateway payload validation and fail-closed configuration.
- Historical OI is deliberately excluded.

## Gateway contract — remaining external integration

The application-side adapter expects the configured gateway to implement `GET /order-flow/snapshot`. The gateway must authenticate its m.Stock session server-side, renew tokens as required, own the WebSocket connection and binary packet decoder, subscribe to relevant futures/options instruments, reconnect with backoff, and return a normalized JSON snapshot in this shape:

```json
{
  "status": "success",
  "data": {
    "last_tick_at": "2026-11-13T10:00:00+05:30",
    "futures_contracts": [
      {
        "symbol": "NIFTY",
        "expiry": "2026-11-26",
        "price": 25000.0,
        "volume": 1200,
        "oi": 450000,
        "previous_oi": 430000
      }
    ],
    "option_contracts": [
      {"strike": 25000, "option_type": "CE", "oi": 12000},
      {"strike": 25000, "option_type": "PE", "oi": 14000}
    ]
  }
}
```

The gateway must source these values from verified provider fields and preserve the exchange timestamp. Do not infer option OI from an undocumented field, fabricate missing ticks, or report a stale/disconnected feed as live. Browser clients never receive m.Stock API keys or access tokens. If the gateway is absent or unavailable, the API returns 503 and the UI clearly shows **NOT CONNECTED** while retaining the demo disclaimer.

**Deployment and integration status (verified 13 November 2026):** The existing EC2 gateway directory was inspected through the user's AWS Systems Manager session. It contains `mstock_stream.py` (Type A binary-frame decoder), `market_stream.py` (persistent WebSocket worker), and `market_stream_routes.py` (read-only Flask routes). The user confirmed the m.Stock account uses **Type A**. The gateway's `app.py` imports and registers `create_market_stream_blueprint` (reported at lines 917–924), and `mstock-gateway.service` was observed active. These are deployed-host observations; they do not establish that the files are committed to this application repository.

The Flask blueprint exposes `/market-stream/start`, `/market-stream/stop`, `/market-stream/status`, and `/market-stream/snapshot`. Its worker must be started with an explicit token subscription; blueprint registration and an active systemd process do not prove the worker is connected or receiving ticks. The diagnostic request returned `GATEWAY_SECRET_INVALID`, so gateway-route authentication/status has not yet been verified. No live WebSocket tick receipt has yet been demonstrated.

**Order Flow integration remains incomplete:** the Financial OS adapter documented above expects `GET /order-flow/snapshot` and a normalized futures/options JSON contract, while the inspected EC2 Flask blueprint exposes `/market-stream/snapshot` with a raw tick-cache response. No verified adapter/route mapping between those contracts has been established. The gateway shared-secret mismatch must also be resolved using the existing server-side configuration; do not expose or regenerate credentials. Do not mark the Order Flow panel LIVE until subscriptions, fresh ticks, normalized adapter output, backend authentication and frontend display are all verified.

The old Sydney-host HTTP 502 handshake observation remains historical evidence only; it is not proof of the current worker's status. Do not change trading/order execution, existing REST market-data routes, database state or migrations while completing this read-only integration check.

## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Any commercial use requires a separate licence from the rights holder.
