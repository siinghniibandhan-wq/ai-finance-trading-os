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

The application-side adapter now reads the existing authenticated `GET /market-stream/snapshot` raw tick cache and `GET /instruments` CSV from the configured m.Stock gateway. It joins ticks to the provider instrument master by instrument token and maps futures/options only when provider metadata and full-packet tick fields are present. The gateway still owns m.Stock authentication, WebSocket lifecycle, Type A decoding, subscriptions and reconnects. The application does not invent missing contract identity, previous OI, or price scaling. The Type A decoder currently exposes raw LTP, so the application labels it `price_raw` until the provider's exact price divisor is verified.

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

**Deployment and integration status (verified 13 November 2026):**

The user's AWS Systems Manager session confirmed the following on the EC2 gateway host:

- mstock-gateway.service is active. The Flask application runs as PID 76459 and listens on 127.0.0.1:8000.
- The gateway app registers create_market_stream_blueprint; the blueprint exposes read-only /market-stream/start, /stop, /status and /snapshot routes.
- The stream worker runs as a background thread inside the Flask application, not as a separate operating-system process. Its authenticated status response reports running=true.
- Gateway authentication is now verified for the diagnostic request: a request carrying X-Financial-OS-Gateway-Secret with the secret read directly from the running process's FINANCIAL_OS_GATEWAY_SECRET returned HTTP 200. The earlier HTTP 403 came from unauthenticated curl requests that omitted the required header. Both FINANCIAL_OS_GATEWAY_SECRET and MSTOCK_GATEWAY_SECRET variable names were present in the running process; secret values were not displayed.
- The authenticated /market-stream/status response reported connected=false, stale=true, cached_instruments=0, no last tick timestamp, reconnect_count=933, mode=3 (full) and subscribed token 2885. The instrument identity for token 2885 has not been independently verified.
- The authenticated /market-stream/snapshot route returned HTTP 200 with an empty ticks array.
- DNS for ws.mstock.trade resolved to provider AWS load-balancer addresses in Mumbai (ap-south-1). TCP/TLS connectivity and certificate verification succeeded using TLS 1.3. No outbound proxy variables were configured. websocket-client version 1.9.0 is installed.
- The worker's WebSocket handshake to wss://ws.mstock.trade repeatedly receives HTTP 502 from a server identifying as awselb/2.0. The failure occurs during the HTTP upgrade, before the worker sends LOGIN, subscribe or mode messages. No ticks have been received.

**Current result: the gateway and its internal authentication work, but the upstream m.Stock WebSocket transport is disconnected. The Order Flow feed is NOT LIVE.** This 502 is not evidence of invalid m.Stock credentials, a decoder defect or a failed subscription because the handshake has not completed.

The user has already contacted m.Stock and is waiting for its response. Do not resend duplicate support requests while waiting. Once a provider response or new handshake evidence is available, resume with a controlled connection test. Do not restart services, change credentials, move regions, alter the decoder or change trading/order execution without evidence and explicit approval.

**Order Flow integration remains incomplete:** the application adapter expects GET /order-flow/snapshot with normalized futures/options data, while the EC2 Flask blueprint currently exposes /market-stream/snapshot with raw decoded tick-cache data and stream status. No verified mapping from raw ticks to the normalized contract has been established. The token master/expiry mapping and provider packet-field validation also remain outstanding. Do not invent tokens, infer undocumented OI fields, or report LIVE until fresh subscriptions, valid decoded ticks, normalized adapter output, backend authentication and frontend freshness display are verified end-to-end.

The current application-side hardening changes are in draft PR #188. Local test execution and CI status must be checked on the exact PR head before describing those changes as verified.
## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Any commercial use requires a separate licence from the rights holder.
