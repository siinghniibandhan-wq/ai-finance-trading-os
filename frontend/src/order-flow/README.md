# Market Flow

Market Flow is a live, read-only derivatives workspace. It is separate from the **Markets** page, which continues to use the existing m.Stock REST quote and market-overview APIs.

## Shared m.Stock login

- Financial OS sign-in remains the application's Bearer-token authentication.
- The m.Stock broker session is authenticated once through `POST /api/market-broker/authenticate`, which forwards the six-digit TOTP to the gateway's `POST /auth`.
- The gateway keeps the resulting broker access token in its existing process-level session. Its REST quote endpoints and the SDK WebSocket worker both use that same token.
- `GET /api/market-broker/status` reads the gateway's `GET /auth/status` endpoint without exposing the access token.
- When a new TOTP login replaces the access token, the gateway worker must recreate its SDK connection so it does not keep using the old token.

## Live data path

```text
Markets page
  └─ Financial OS REST APIs
       └─ m.Stock Gateway REST (/quote, /index-quote, /gainers-losers, ...)

Market Flow page
  └─ Browser WebSocket (/api/order-flow/stream)
       └─ FastAPI validates the existing Financial OS Bearer session
            └─ Order Flow adapter
                 ├─ /instruments (verified instrument master)
                 ├─ POST /market-stream/start (idempotent subscription)
                 └─ /market-stream/snapshot (gateway's live tick cache)
                      └─ m.Stock SDK WebSocket worker
                           └─ wss://ws.mstock.trade
```

The browser no longer polls `GET /api/order-flow/snapshot`. It receives snapshots over the authenticated WebSocket. The backend starts the gateway subscription on the first stream read and then relays the gateway's latest decoded snapshot at one-second intervals. The gateway remains the owner of the upstream m.Stock WebSocket connection and reconnect lifecycle.

The browser sends the existing Financial OS access token in the WebSocket subprotocol, not in the URL. Broker credentials and the gateway shared secret never reach the browser.

## Data integrity

Only a successful snapshot with a fresh, verified feed is displayed as LIVE. The workspace currently displays provider-backed:

- Futures contract, expiry, last traded price and provider-computed percentage change
- Futures session OHLC, volume, average traded price, open interest, provider OI high/low, and total bid/ask depth quantities with a derived depth balance (not executed trades)
- Option contracts, strike, CE/PE side, price, provider-computed percentage change, volume and open interest
- Aggregated CE/PE open interest by underlying, expiry and strike (contracts are never mixed across symbols)
- Feed connection and freshness

The current gateway adapter does not provide verified spot percentage change, intraday historical candle series, previous-session OI, OI change, PCR history, support/resistance or conviction signals. Those values are not generated or filled with demo data. Missing provider fields remain unavailable.

The adapter follows the bundled Type A SDK field names: `last_price`, `volume_traded`, `change`, `ohlc`, and `open_interest`. The SDK currently emits its `open_interest`, `open_interest_high` and `open_interest_low` values as one-element tuples; the adapter unwraps only that documented one-element representation. The SDK's `change` is its percentage change against the OHLC close, so it is exposed as `change_pct`. Price scaling is not applied a second time to SDK-decoded values.

Unknown instrument tokens are not assigned guessed symbols.

## Deployment and verification requirements

- The matching EC2 gateway changes are in the separate `mstock-gateway-update.zip` package. They add shared-secret checks for the broker-auth and market REST/instrument endpoints, `/auth/status`, and SDK reconnection when the broker token changes.
- The gateway's `FINANCIAL_OS_GATEWAY_SECRET` and Financial OS backend's `MSTOCK_GATEWAY_SECRET` must match.
- The backend reverse proxy must support WebSocket Upgrade for `/api/order-flow/stream`.
- Do not report LIVE until the upstream WebSocket is connected, the SDK login/subscription succeeds, fresh ticks arrive, and the normalized futures/options data reaches this page.

The uploaded gateway archive's `mticker.log` contains repeated WebSocket close code `1006` events. That indicates an abnormal connection close but does not, by itself, identify whether the cause is the provider, network path or SDK. A fresh post-deployment end-to-end check is still required.

## Attribution and licence

The legacy Flow Diagram source is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. The current live Market Flow page does not render the legacy simulated board.
