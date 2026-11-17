# Order Flow workspace

The Financial OS navigation exposes **Order Flow** separately from the existing **Markets** workspace. Existing Markets, portfolio and broker order workflows remain separate and unchanged.

## Phase 1 — interactive board

The workspace includes the responsive Flow Diagram, ranked bullish/bearish instruments, sector highlighting, linked chart/list focus, pinned instrument details, option OI profile, support/resistance, conviction checks, keyboard navigation and persistent universe/instrument preferences.

The source project's interaction/layout model has been adapted to Financial OS; this is not a verbatim component transplant.

## Phase 2 — implemented application-side work

- Pure backend transformations for futures contract-month aggregation and strike-wise CE/PE OI aggregation. OI change/percentage is calculated only when a verified previous-OI value is supplied.
- Feed freshness classification: `fresh`, `stale`, `disconnected`.
- Authenticated, read-only API: `GET /api/order-flow/snapshot?symbol=NIFTY`.
- Server-side adapter reusing `MSTOCK_GATEWAY_URL` and `MSTOCK_GATEWAY_SECRET`; no separate derivatives gateway or secret is required.
- Frontend feed panel with authenticated polling, exchange-timestamped live futures price history, live CE/PE OI-by-strike bars, freshness display and bounded exponential retry (10–60 seconds).
- Backend tests for aggregation, freshness, gateway payload validation and fail-closed configuration.
- Historical OI is deliberately excluded.

## Existing gateway contract and normalization

Financial OS reuses the existing `MSTOCK_GATEWAY_URL` and `MSTOCK_GATEWAY_SECRET`. It calls the deployed Flask gateway's authenticated read-only `GET /market-stream/snapshot` endpoint and the existing `GET /instruments` CSV endpoint. The browser never receives broker credentials or the gateway secret.

The market-stream snapshot returns top-level `status`, `ticks` and `stream` fields. Type-A decoded ticks carry the instrument `token`, `last_price`, `volume`, `open_interest`, `exchange_timestamp` and `received_at`. The gateway's instrument-master CSV includes `instrument_token`, `tradingsymbol`, `name`, `expiry`, `strike`, `instrument_type`, `segment` and `exchange`.

The adapter resolves each tick token against the instrument master, classifies `FUT*` and `OPT*` instruments, reads the underlying from the master `name` field, and derives CE/PE only from the option trading-symbol suffix. Missing or unknown token metadata is counted as unmapped; contract identity is never guessed.

The Type-A decoder already applies the `1/100` price divisor. The adapter passes `last_price` through unchanged. Type-A exchange timestamps are seconds since `1980-01-01 UTC` and are converted to timezone-aware ISO-8601 timestamps before freshness evaluation. Current OI and volume are read from the decoded tick. A previous-session OI baseline is not supplied by this snapshot, so OI change is not fabricated.

The authenticated Financial OS endpoint remains `GET /api/order-flow/snapshot` and retains the existing Bearer-session dependency. It returns mapped futures contracts, contract-month aggregates and strike-wise CE/PE OI. The UI plots real futures price observations captured on new exchange timestamps and real current option OI by strike. The broader sector/conviction/flow-board demo indicators remain explicitly labelled simulated because the gateway snapshot does not provide historical candles or the full derived analytics inputs.

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

**Order Flow integration status:** The application-side adapter now calls the existing GET /market-stream/snapshot endpoint using the existing X-Financial-OS-Gateway-Secret header. It accepts decoded ticks and normalizes only records that explicitly include instrument_type/segment, symbol, expiry, price, volume and OI; option rows additionally require strike and CE/PE side. It exposes mapped futures and strike-wise option OI to the authenticated Order Flow API and displays those values in the frontend live-feed panel. Token-only or incomplete records are counted as unmapped and are never assigned guessed instrument identities. Prices are passed through as gateway-decoded values without a second divisor being applied. The wider demo flow board remains explicitly labelled demo analytics because a single latest snapshot does not supply historical candles or a verified full-universe instrument map. The EC2 gateway's last verified snapshot was empty and its upstream WebSocket handshake was returning HTTP 502; therefore no live ticks or live charts can currently be verified. Token-to-contract mapping is now implemented against the gateway instrument master, but has not yet been verified against a fresh production tick set. A successful upstream WebSocket handshake and non-empty authenticated snapshot remain required before live chart rendering can be verified. Do not invent tokens, infer undocumented OI fields, or report LIVE until fresh subscriptions, valid decoded ticks, normalized adapter output, backend authentication and frontend freshness display are verified end-to-end.

The current application-side hardening changes are in draft PR #188. Local test execution and CI status must be checked on the exact PR head before describing those changes as verified.
## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Any commercial use requires a separate licence from the rights holder.
