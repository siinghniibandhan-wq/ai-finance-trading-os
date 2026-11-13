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

**Not included:** historical OI, actual m.Stock WebSocket packet decoding, provider credential setup, gateway deployment, AWS changes, production changes or broker/order execution changes. The repository has no gateway worker implementation, and the provider binary decoder cannot be safely completed without a verified sample packet and field/scaling specification. The live panel becomes LIVE only after the external gateway is connected and supplies fresh validated ticks.

## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Any commercial use requires a separate licence from the rights holder.
