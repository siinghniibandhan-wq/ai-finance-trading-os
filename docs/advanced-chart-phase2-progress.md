# Advanced Chart Phase 2 — REST-only implementation status

Baseline implementation: merged to `main` through PRs #219, #220 and #222 (18–19 November 2026). Current REST analytics completion work is on `feature/complete-rest-market-analytics`; it is not merged or production-deployed.  
PR #219 merge: `aa1b8261d670d91622f9e59060634a619af45dfa`  
PR #220 merge: `3911c70dddb643e0c2fa7d700d9bb444a4c2d156`  
PR #222 merge: `6ac5571ecccf8f954a99342240409e3dfdfc986a`

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
- Existing Markets tab and existing market overview workflow are preserved. The REST Chart Flow workspace is implemented separately through `GET /api/market-flow/` and is registered as an authenticated backend route.

## Current integrated Chart Flow and market overview state (19 November 2026)

- Chart Flow backend route: `backend/app/routes/market_flow.py`, registered in `backend/app/main.py` behind the authenticated-user dependency.
- The market snapshot combines provider-ranked NSE/BSE cash-market gainers and losers with supported index snapshots. The frontend requests sector index snapshots by default, and sector-specific provider-ranked mover lists are available on selection.
- Sector requests return the provider's ranked movers for the selected sector and an index quote; they do not represent every constituent in that sector.
- The route enforces pacing for m.Stock mover requests, caches eligible complete sector/index responses, returns partial status and provider errors when only part of the snapshot succeeds, and declares the operation read-only with no database writes.
- The backend currently configures 17 provider-documented NSE sector universes. Sector index quotes now use the gateway's `/quote?symbol={EXCHANGE}:{SYMBOL}` route, whose best-effort Type A OHLC enrichment supplies previous close when available; the backend derives daily index change only from that provider OHLC close. The former `/index-quote` route only proxied LTP and could not reliably provide previous-close performance. The source-level correction and regression test are on `feature/complete-rest-market-analytics`; live provider coverage remains unverified until an authenticated production smoke test.
- Full exchange advance/decline breadth, full sector constituent breadth, delivery statistics and historical market-flow history are not supplied by the current endpoint. UI counts must be described as provider-returned mover rows, not total listed-market breadth.
- PR #220 consolidated the Market overview feed and its REST refresh lifecycle. PR #222 added the REST sector explorer and safe provider integration. Both are merged to `main`.
- Chart Flow remains REST-only and excludes intraday history reconstruction and continuous market streaming. Advanced Chart historical OHLCV and quote snapshots are a separate instrument-analysis workflow.

## REST provider contracts — documentation vs application wiring

- m.Stock publishes Type A REST routes for both option-chain master and option-chain data:
  - `GET /openapi/typea/getoptionchainmaster/{exch}`
  - `GET /openapi/typea/GetOptionChain/{exch}/{expiry}/{token}`
- The Type A documentation page labels the option-chain feature “Coming Soon” and explicitly labels the master endpoint “coming soon”. It nevertheless documents the data endpoint, its request headers, and an example response containing `call`, `put`, `future`, and `spot` fields. Documentation and SDK route declarations establish that the API is published; they do not establish production enablement for this account.
- The official m.Stock Type A Python SDK includes `option_chain_master` and `option_chain_data` route definitions. The official Type A Node SDK also exposes option-chain methods. Therefore the earlier statement that Type A has no documented option-chain REST capability was incorrect.
- Type B publishes corresponding option-chain REST paths under `/openapi/typeb/`, with Type B-specific authentication. Its documentation also marks the option-chain master as “coming soon”. Type B is not part of this implementation.
- The Type A example option-chain payload lists call/put contract rows as compact strings and includes a futures token and spot identifier. It does not establish OI, OI change, volume, IV, Greeks, or historical OI fields. The documented Type A historical REST endpoint returns OHLCV candles (maximum 1,000 bars/request), not OI history. These fields must be confirmed from live Type A responses and/or separately documented Type A REST fields before analytics are implemented.
- The Financial OS backend now exposes authenticated `/api/options-hub/master` and `/api/options-hub/chain` routes. The saved gateway variant implements these as a Script Master + batched LTP quote adapter; it does not call the provider's documented Type A option-chain route. This application adapter is distinct from the provider's still-coming-soon option-chain API, and its deployment/account runtime remains unverified.
- No production request has yet been made against the user's authenticated Type A account in this work session. Endpoint availability, subscription entitlement, actual response schema, quote enrichment and delivery-statistics availability remain unverified. The official Type A docs specify 1 data API request/second and 20 quote API requests/second; these are distinct rate-limit buckets.
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
| Type A option-chain data | Financial OS authenticated REST adapter added for gateway `/options/chain`; depends on gateway route deployment and provider response | App wiring implemented; gateway/account runtime unverified |
| CE/PE option prices and volume | Gateway options-enabled variant parses Script Master contracts and batches LTP quotes | Adapter implemented; live quote coverage unverified |
| CE/PE open interest | Gateway passes through `open_interest` only when present in provider quote | Optional field; complete live coverage unverified |
| PCR, Max Pain and strike OI distribution | Frontend model and strike chart implemented; calculations require complete CE/PE OI at every strike | Implemented with strict completeness gate; live data unverified |
| Futures price + OI history | No verified historical Type A REST response contract in this application | Not yet verified |
| Sector index performance | 17 configured sector symbols; backend uses the gateway `/quote` LTP + best-effort OHLC path and derives change from provider previous close | Implemented in source; live symbol coverage and account response unverified |
| Sector ranked movers | Type A Top Gainers/Losers SecurityIdCode mappings for 17 sectors | Implemented; live request coverage unverified |
| Full sector constituents / sector breadth | No complete constituent membership and full-universe advances/declines REST feed | Not available from current integration |
| Full-market breadth | Bounded top-movers endpoint is not a full market universe | Not available from current integration |
| Historical OI time series | No verified historical OI REST response contract in this application | Not yet verified |
| Continuous live ticks | Excluded by the REST-only product requirement | Not in scope |

## Current completion branch notes (19 November 2026)

- Branch: `feature/complete-rest-market-analytics`, based on `main`.
- Regression test added for the OHLC-enriched gateway `/quote` route; backend index retrieval changed from LTP-only `/index-quote` to `/quote?symbol={EXCHANGE}:{SYMBOL}`. This allows sector and benchmark percentage change to be calculated from actual provider OHLC close when returned.
- The old architecture draft has been replaced with the current source architecture: Markets, Order Flow/Chart Flow, Advanced Chart and Options Hub; authenticated `apiFetch`; FastAPI private routes; gateway shared-secret boundary; REST-only transport; no intraday Chart Flow.
- Added authenticated Financial OS REST routes `/api/options-hub/master` and `/api/options-hub/chain`, forwarding through the existing gateway shared-secret boundary to `/options/master` and `/options/chain`. Added an independently authored Options Hub UI with exchange/underlying/expiry selection, strike-wise CE/PE table, mirrored OI chart and PCR/Max Pain calculations gated on complete two-sided OI.
- Added backend proxy tests and frontend options-model tests; CI now includes the Options Hub model test. The saved options-enabled gateway source contains the required upstream routes, but their presence on the active AWS gateway and actual m.Stock account response remain unverified. If the gateway does not expose these paths, the UI surfaces an unavailable state; it does not use mock data.
- The branch has passed CI at its earlier implementation head. Subsequent sample-scope regression assertions and documentation corrections have been pushed and require a fresh CI run. The branch is not merged or deployed. No production endpoint result is claimed.
- The latest API metadata explicitly labels market movers as `provider_ranked_sample`, sets `market_summary.sample_only=true` and `breadth_complete=false`, and corrects the sector limitation text to reflect the OHLC-enriched `/quote` route. A regression test now asserts these guarantees.

## Integrity and preservation constraints

- No simulated or hardcoded market values.
- No equity volume used as a proxy for futures OI.
- No spot values substituted for futures contracts.
- No option-chain PCR, writer positioning or OI-derived support/resistance without actual option-chain observations.
- Exchange timestamps must remain distinct from backend retrieval timestamps.
- Preserve existing Bearer authentication, shared-secret validation, Markets tab, chart workflows and broker-order safeguards.
- No AWS deployment, secrets, credentials or runtime configuration changes were part of PRs #219, #220 or #222.
- MrChartist source/assets are not copied; its licence remains a separate commercial-use gate.

## Verification

- PR #219, #220 and #222 are merged to `main` (merge SHAs above).
- CI passed for the reviewed PR commits before merge. PR #223 later passed both Financial OS CI and Frontend production build before the Amplify cutover documentation/code changes were merged.
- User-provided screenshots dated 19 November 2026 show the Amplify-hosted application rendering Markets, Chart Flow and Advanced Chart views. They are UI evidence, not a substitute for a live backend/provider contract test or a formal production smoke-test record.
- The current source route and frontend integration are repository evidence; live provider completeness and EC2/Nginx state remain separate verification items.
