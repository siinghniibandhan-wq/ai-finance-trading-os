# Advanced Chart Phase 2 — REST-only implementation status

Branch: `feature/market-flow-chart-suite-stage-1`  
PR: #219 (draft; not merged)

## Data transport policy

- Market data transport is REST API only.
- Do not add WebSocket connections, socket clients, streaming workers, subscriptions, event-stream transports or streaming caches to this feature.
- Frontend market data must use the existing authenticated REST API client and backend market routes.
- Refreshes are bounded REST requests. A quote snapshot is a point-in-time response, not a continuous tick feed.
- TradingView Lightweight Charts crosshair and chart-event subscriptions are local chart-library interactions; they are not network sockets or market-data transports.

## Implemented

- Gainer and Loser Scanner views use authenticated `GET /api/market-movers/` with provider-row validation, symbol/company search, NSE/BSE filter, ranked percentage bars, reported-volume summary and bounded 30-second REST refresh while visible.
- Scanner row selection opens the existing Advanced Chart with the selected instrument.
- Price chart modes: Candlestick, OHLC Bar, Line, Area and Heikin-Ashi (derived from validated provider OHLC).
- Technical overlays: SMA 20, EMA 20, Bollinger Bands (20, 2) and intraday VWAP. VWAP resets by India trading-session date and requires positive volume on every candle.
- Indicator pane: RSI 14 and MACD (12, 26, 9), derived from loaded provider closes.
- Historical OHLCV uses authenticated `GET /api/market-charts/`; the LTP marker refreshes from authenticated REST quote snapshots.
- Existing Markets tab and existing Market Flow board/workflow are preserved.

## REST provider contracts — documentation vs application wiring

- m.Stock publishes Type A REST routes for both option-chain master and option-chain data:
  - `GET /openapi/typea/getoptionchainmaster/{exch}`
  - `GET /openapi/typea/GetOptionChain/{exch}/{expiry}/{token}`
- The Type A documentation page labels the option-chain feature “Coming Soon” and explicitly labels the master endpoint “coming soon”. It nevertheless documents the data endpoint, its request headers, and an example response containing `call`, `put`, `future`, and `spot` fields. Documentation and SDK route declarations establish that the API is published; they do not establish production enablement for this account.
- The official m.Stock Type A Python SDK includes `option_chain_master` and `option_chain_data` route definitions. The official Type A Node SDK also exposes option-chain methods. Therefore the earlier statement that Type A has no documented option-chain REST capability was incorrect.
- Type B publishes corresponding option-chain REST paths under `/openapi/typeb/`, with Type B-specific authentication. Its documentation also marks the option-chain master as “coming soon”. Type B is not part of this implementation.
- The Type A example option-chain payload lists call/put contract rows as compact strings and includes a futures token and spot identifier. The example alone does not establish that OI, OI change, volume, IV, Greeks, or historical OI are included in that response. Those fields must be confirmed from live Type A responses and/or separately documented Type A REST quote fields before analytics are implemented.
- The current Financial OS gateway integration does not yet expose Type A option-chain routes, and the Financial OS backend has no option-chain route. This is an application-wiring gap, not proof that the provider's Type A REST capability is absent.
- No production request has yet been made against the user's authenticated Type A account in this work session. Endpoint availability, subscription entitlement, actual response schema, rate limits, and required quote enrichment remain unverified.
- Sector constituent membership, a complete listed-market advance/decline universe, and historical OI series must be treated as separate data requirements; they are not established by the option-chain endpoint examples.

## Capability status

| Capability | Current evidence | Status |
|---|---|---|
| Equity/spot gainers and losers | Existing Type A gateway route and backend `GET /api/market-movers/` | Implemented |
| Market index snapshots | Existing gateway `/index-quote` and backend index/overview routes | Snapshot only |
| Historical OHLCV | Existing gateway historical route and backend `GET /api/market-charts/` | Implemented |
| Latest quote / LTP marker | Authenticated REST quote snapshot | Implemented |
| Technical indicators | Deterministic derivations from loaded OHLCV | Implemented |
| Type A option-chain master | Documented Type A REST route; documentation explicitly says “coming soon” | Published, runtime availability unverified |
| Type A option-chain data | Documented Type A REST route and sample CE/PE contract response; not wired through current gateway/backend | Published, runtime availability unverified |
| CE/PE option prices, OI and volume | Must be confirmed from actual chain and per-contract Type A REST quote responses | Not yet verified |
| PCR, Max Pain and strike OI distribution | Requires complete, valid CE/PE OI for one expiry | Not yet implementable until live fields are verified |
| Futures price + OI history | No verified historical Type A REST response contract in this application | Not yet verified |
| Sector index performance | Index quote capability exists, but no verified sector-index symbol universe / historical index-token contract has been validated end-to-end | Not implemented |
| Sector constituents / sector breadth | No verified constituent mapping or full-universe advances/declines REST feed | Not available from current integration |
| Full-market breadth | Bounded top-movers endpoint is not a full market universe | Not available from current integration |
| Historical OI time series | No verified historical OI REST response contract in this application | Not yet verified |
| Continuous live ticks | Excluded by the REST-only product requirement | Not in scope |

## Integrity and preservation constraints

- No simulated or hardcoded market values.
- No equity volume used as a proxy for futures OI.
- No spot values substituted for futures contracts.
- No option-chain PCR, writer positioning or OI-derived support/resistance without actual option-chain observations.
- Exchange timestamps must remain distinct from backend retrieval timestamps.
- Preserve existing Bearer authentication, shared-secret validation, Markets tab, chart workflows and broker-order safeguards.
- No AWS deployment, secrets, credentials or runtime configuration changes in this PR.
- MrChartist source/assets are not copied; its licence remains a separate commercial-use gate.

## Verification

- CI on commit `b59f76f`: frontend production build, frontend regression checks, backend regression tests and repository secret scan passed.
- The latest documentation/UI-copy updates require fresh PR checks.
- No production/runtime smoke test is claimed.
