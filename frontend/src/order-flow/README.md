# Order Flow workspace

The Financial OS navigation exposes **Order Flow** separately from the existing **Markets** workspace. Existing Markets, portfolio and broker order workflows remain separate and unchanged.

## Phase 1 — interactive board

The workspace includes the responsive Flow Diagram, ranked bullish/bearish instruments, sector highlighting, linked chart/list focus, pinned instrument details, option OI profile, support/resistance, conviction checks, keyboard navigation and persistent universe/instrument preferences.

The source project's interaction/layout model has been adapted to Financial OS; this is not a verbatim component transplant.

## Phase 2 — implemented application-side work

- Pure backend transformations for futures contract-month aggregation, current OI change/percentage, and strike-wise CE/PE OI aggregation.
- Feed freshness classification: `fresh`, `stale`, `disconnected`.
- Authenticated, read-only API: `GET /api/order-flow/snapshot?symbol=NIFTY`.
- Server-side adapter for the production `/market-stream/*` routes, using the existing gateway URL/secret and verified instrument-master token mapping.
- Frontend feed status panel with authenticated polling, freshness display and bounded exponential retry (10–60 seconds).
- Backend tests for aggregation, freshness, gateway payload validation and fail-closed configuration.
- Historical OI is deliberately excluded.

## Production m.Stock gateway contract

The Financial OS backend now adapts the production Flask gateway contract instead of expecting the obsolete normalized `/order-flow/snapshot` route.

1. Read the gateway's `/instruments` CSV and validate derivative instrument metadata (token, exchange, segment, underlying, expiry, strike, option side and lot size).
2. Select the active Order Flow underlying's verified futures/options tokens, capped at 200; a request without a symbol uses a balanced derivative universe.
3. Idempotently call authenticated `POST /market-stream/start` with `{"tokens":[...],"mode":3}`. The gateway worker retains its SDK connection and reconnect lifecycle.
4. Read authenticated `GET /market-stream/snapshot`, which returns `ticks` plus `stream` status.
5. Join each decoded SDK tick to the verified instrument master and normalize futures, options, price, volume, OI and timestamps for the existing Order Flow API.

The backend uses the existing `MSTOCK_GATEWAY_URL` and `MSTOCK_GATEWAY_SECRET` settings and the existing `X-Financial-OS-Gateway-Secret` header. It does not require a second derivatives-gateway URL or expose broker credentials to the browser. The existing Bearer authentication on `GET /api/order-flow/snapshot` remains unchanged.

The SDK supplies decoded prices; the adapter does not divide or rescale them again. OI is taken only from the SDK's `oi` field. The stream does not supply previous-session OI, so the adapter does not invent `previous_oi` or OI change. Historical OI remains excluded. Unknown tokens are counted as unmapped rather than assigned a guessed identity.

The frontend reports LIVE only when the gateway reports a verified connected stream and the last tick is fresh. Empty, stale or disconnected snapshots remain NOT CONNECTED/STALE; demo charts and derived indicators remain labelled simulated.

**Current upstream limitation:** the latest verified EC2 diagnostics recorded an HTTP 502 during the m.Stock WebSocket upgrade, before LOGIN or subscription acknowledgement. No live ticks were received in that diagnostic. The backend adapter can now request subscriptions and normalize returned ticks, but it cannot make the provider's WebSocket handshake succeed. Until a fresh authenticated tick is observed end-to-end, the feed must remain NOT LIVE.

The adapter changes are on branch `fix/order-flow-market-stream-contract`. They are not deployed to the backend and must not be described as live until tests, CI, review and deployment are complete.

## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Any commercial use requires a separate licence from the rights holder.
