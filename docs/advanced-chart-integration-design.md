# Markets Analytics Integration — Architecture & Implementation Specification

> **Approved navigation structure — 19 November 2026 (supersedes conflicting navigation references below):**
>
> The Markets section has exactly four main workspaces:
> 1. **Market** — existing market overview; preserve its current behaviour.
> 2. **Order Flow** — whole-market discovery. **Chart Flow is a view within this workspace**, not a separate main tab and not part of Advanced Chart.
> 3. **Advanced Chart** — individual-instrument technical analysis and interactive OHLCV charting.
> 4. **Options Hub** — options-chain and derivatives analysis as a separate workspace.
>
> Chart Flow must be implemented inside `frontend/src/features/order-flow/`. Do not add a Chart Flow navigation item under Advanced Chart or create a fifth Markets tab. Options Hub is the fourth Markets navigation item. All new market data access is REST-only; do not introduce WebSockets or streaming in this scope. Existing Market and Advanced Chart workflows remain unchanged.


**Status:** Design draft for review  
**Target repository:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Reference project:** `MrChartist/order-flow`  
**Scope:** Add the full Order Flow-style market visualisation as a new **Advanced Chart** workspace under Markets, without changing the existing Markets workflow.

## 1. Outcome required

The end state is a working, interactive market-analysis workspace—not a collection of quote cards or static dashboard tiles. It must reproduce the reference project's core visual workflow: a market-wide flow view, interactive symbol focus, futures price/OI build-up interpretation, option-chain positioning by strike, support/resistance and a detailed intraday candle chart. It must use Financial OS/m.Stock data wherever that data is genuinely available.

No synthetic prices, fabricated OI, fake candles, placeholder indicators presented as live, or silently substituted demo feeds are permitted. If a data capability is unavailable, the UI must say so explicitly and the missing provider capability is tracked as a blocker/gap.

## 2. Repository findings (inspected default-branch snapshot)

### Financial OS

- React 18 + Vite frontend is under `frontend/`; the main application/navigation is in `frontend/src/App.jsx`.
- The current navigation has one **Markets** section with one **Markets** item. The existing Markets page/workflow is embedded in the large application module.
- The frontend already centralises authenticated requests in `frontend/src/api.js` (`apiFetch`). New protected API calls must use this existing mechanism; do not introduce a second auth/session implementation.
- Frontend dependencies currently include React and lucide-react; no dedicated charting library is listed in `frontend/package.json`.
- Existing backend market routes include:
  - `backend/app/routes/market_quote.py` — latest quote through the shared market-price service.
  - `backend/app/routes/market_history.py` — resolves an instrument from the gateway instrument master and requests historical candles.
  - `backend/app/routes/market_charts.py` — transforms historical candles into chart-ready OHLCV records.
  - `backend/app/routes/market_overview.py`, `market_search.py`, and related market routes.
- `market_charts.py` delegates to `get_market_history`; the history route accepts NSE, NFO, BSE and BFO and the intervals minute, day, 3minute, 5minute, 10minute, 15minute, 30minute and 60minute.
- The current quote response preserves provider quote details (including fields such as OHLC, volume, buy/sell quantities and market depth when actually returned). It explicitly says its retrieval timestamp is not the provider's exchange timestamp.
- The existing chart/history path is read-only and uses the configured m.Stock gateway. Gateway URL, secret, Bearer auth, and deployment configuration are outside this change.

### MrChartist reference project

The inspected repository is `MrChartist/order-flow`, default branch `main`. Its documented and source-tree structure includes:

- `src/features/market-flow/MarketFlowPage.tsx`
- `FlowBoard.tsx`, `FlowChart.tsx`, `FlowDiagram.tsx`, `FlowParts.tsx`, `FlowPopup.tsx`, `FlowSectors.tsx`, `FlowSide.tsx`, `FlowStatus.tsx`
- Separate market-flow model/layout/focus/feed modules and tests.
- A market-wide distribution/flow chart; bullish and bearish paths; sector distribution; symbol tiles; pinned symbol detail; 5-minute candles; option OI profiles; support/resistance and build-up interpretation.
- Its README documents multiple providers, including demo, NSE archive, recorded sessions, generic HTTP and Upstox. The demo provider is explicitly simulated. The archive's end-of-day OHLC is real, but its intraday path is reconstructed; it is not genuine tick-by-tick intraday history.
- The source project describes an option chain, futures, historical candle and OI data pipeline. These are reference capabilities, not proof that Financial OS currently exposes all those fields.

### Critical licensing constraint

The reference repository's `LICENSE` is **PolyForm Noncommercial 1.0.0** and its required notice says commercial use requires a separate licence from Mr. Chartist. Therefore this integration must not copy or port its source code, assets, styling, logos, or other copyrightable implementation into a commercial/proprietary Financial OS unless the appropriate separate licence is obtained. The implementation plan is to build a clean-room, independently authored equivalent from observed product behaviour and documented data contracts, while preserving attribution only where legally required. If the intended use is commercial and the user wants the original code copied/ported, obtain written permission/licensing first.

## 3. Proposed architecture

### Navigation and isolation

- Add **Advanced Chart** as a second item inside the existing **Markets** navigation section.
- Keep the existing **Markets** item and its component, state, refresh intervals, endpoints, and visual behaviour untouched.
- Mount a new isolated React feature entry, proposed path:
  - `frontend/src/features/advanced-chart/AdvancedChartPage.jsx`
  - `frontend/src/features/advanced-chart/advanced-chart.css`
  - `frontend/src/features/advanced-chart/api.js`
  - `frontend/src/features/advanced-chart/model.js`
  - Additional focused components/hooks/tests as required.
- The only allowed change to existing app navigation/rendering is the minimum registration needed to route to the new item. No broad refactor of `App.jsx`.

### Data flow

```
Advanced Chart workspace
       |
       | authenticated apiFetch
       v
Financial OS Advanced Chart API adapter (new, read-only)
       |
       +---- existing Market Search / instrument master
       +---- existing Market Quote service
       +---- existing Market History / Market Charts routes
       +---- existing m.Stock gateway (through existing backend services)
       |
       +---- future dedicated derivatives/OI/stream adapter, only after provider contract is verified
```

- Browser code must never call m.Stock directly or receive broker secrets/access tokens.
- Reuse existing backend service functions rather than duplicate gateway authentication, instrument lookup, or quote/history retrieval.
- Prefer a small, read-only aggregation/normalisation layer for chart-specific payloads. Keep provider-specific parsing in backend adapters.
- The API contract must carry source, exchange/provider timestamp when available, server retrieval timestamp, freshness/age, interval, instrument identity and field availability.
- Missing fields remain `null`/unavailable. Do not calculate a value from unrelated fields or label retrieval time as exchange time.
- Historical OHLCV is the first verified chart source. Live quote updates can update the current price/last candle only when the provider gives sufficient trustworthy fields. A quote polling loop is not to be described as a continuous tick stream.
- WebSocket/continuous streaming is a separate feed capability: verify actual gateway subscription protocol, authentication, instrument subscription/unsubscription, heartbeat, reconnect, sequence/timestamps and payload schema before wiring it. If unavailable, use a clearly labelled polling fallback using existing quote endpoints, with a configurable and rate-safe cadence.

### Chart rendering

- Choose and integrate a maintained charting engine only after checking its licence, React compatibility, interaction support, bundle cost and ability to render candlesticks, volume, multiple panes, overlays and drawing tools.
- The chart must be a genuine interactive financial chart: pan/zoom, crosshair, time/price scales, symbol and exchange selection, interval selection, OHLCV candles, volume pane, last-price line, and indicator/overlay controls.
- Do not implement the main candlestick chart as decorative SVG, static screenshots, or a row of data cards.
- Advanced overlays and tools must be backed by calculations from actual chart series and must not manufacture input data. If an indicator requires more history than is loaded, request sufficient history or show a clear unavailable state.

## 4. Two implementation phases

### Phase 1 — Reference analysis, integration foundation and verified real-data chart

1. Finish a file-by-file audit of the reference feature, including its feed contract, models, layout, chart interactions, tests, dependencies and licence boundaries.
2. Finish a file-by-file audit of Financial OS Markets navigation/rendering, existing API registration, authentication wrapper, market routes, service contracts, gateway adapter and regression tests.
3. Record a capability matrix for every reference feature: available from current Financial OS, derivable from verified source fields, provider gap, or prohibited/unlicensed source-code reuse.
4. Add the isolated Advanced Chart navigation entry and feature shell.
5. Implement instrument search/selection, interval/range selection, historical OHLCV loading and a full interactive candlestick/volume chart using existing authenticated APIs.
6. Connect live quote updates only through existing Financial OS backend routes. Clearly show live/polling/stale/disconnected state and real source timestamps.
7. Implement only those flow/market breadth and futures/OI visualisations for which actual, correctly identified source data exists. Never infer futures OI from equity quote volume or substitute spot data for futures.
8. Test chart data mapping, date/interval boundaries, empty/error responses, auth expiry, stale feeds, symbol changes and cleanup of timers/subscriptions.
9. Run frontend build and relevant existing market tests/regression checks. Explicitly verify the original Markets view and its refresh behaviour remain unchanged.

**Phase 1 exit criteria:** Advanced Chart is a usable, real-data candlestick workspace with interactive chart controls and volume where supplied; source/freshness is honest; no simulated market data is used; existing Markets remains unchanged. A shell or card-only implementation does not pass.

### Phase 2 — Full market-flow parity and advanced derivatives analysis

1. Implement the market-wide flow/distribution visualisation and interactive symbol focus, using real instrument universe, futures prices and timestamps.
2. Add futures build-up classification only when both comparable futures price and OI observations exist (long build-up, short covering, short build-up, long unwinding).
3. Add per-strike CE/PE option OI profiles, OI change, expiry selection, PCR and writer positioning only after verifying the broker/provider contract and units.
4. Add support/resistance and OI concentration zones from actual option-chain observations, with transparent calculation definitions and tests.
5. Add intraday multi-timeframe candles, historical OI/time series and volume/OI panes where the provider exposes the underlying history. Do not fabricate historical OI from a single snapshot.
6. Add chart indicators, drawing tools, overlays, sector analysis, ranking/filters, hover/pin interactions and responsive layout to match the reference workflow's functional depth.
7. Implement true continuous streaming if the existing gateway/provider supports it. Otherwise retain a clearly identified polling fallback; do not claim continuous streaming.
8. Add integration and regression coverage for stream reconnects, duplicate/out-of-order ticks, market-closed conditions, missing instruments, expiry rolls, stale data and provider outages.

**Phase 2 exit criteria:** The full Advanced Chart workflow is functional end-to-end with real source-backed data for every displayed metric; unsupported provider features are explicitly identified rather than simulated; regression tests prove the original Markets workflow is preserved.

## 5. Data capability matrix — initial evidence

| Capability | Evidence in inspected Financial OS source | Initial decision |
|---|---|---|
| Instrument search/master | Existing market search and history route reads gateway instrument master | Reuse after auditing exact response/selection rules |
| Latest spot/equity quote | Existing quote route and shared market-price service | Reuse; quote timestamp caveat must remain visible |
| Historical OHLCV candles | Existing history and charts routes; m.Stock gateway historical call | Reuse and verify actual response mapping |
| Volume | OHLCV candle contract and quote normalisation include volume fields | Use only when returned and valid |
| Futures price and OI | Not established by inspected quote/history routes alone | Verify derivative instrument resolution and provider responses |
| Option chain CE/PE OI | Not established by inspected Financial OS routes | Provider/API gap until verified |
| OI change / historical OI | Not established by inspected routes | Requires historical observations or a provider history source |
| Continuous WebSocket stream | Not established by the inspected Financial OS route files | Audit gateway worker/subscription implementation before claiming support |
| Exchange-native tick timestamp | Current quote route explicitly says provider market timestamp is unavailable | Do not substitute backend retrieval time |

This matrix is provisional until the remaining gateway, route registration, market page and reference feed/model files have been audited.

## 6. Non-breaking guardrails

- Do not delete, rename, restyle, refactor or change existing Markets components or API behaviour.
- Do not change existing refresh intervals, quote/history contracts, cache rules, gateway secrets, Bearer authentication, AWS/systemd configuration or deployment setup.
- Do not alter unrelated navigation sections, themes, global CSS or app state.
- New feature code must be isolated under `frontend/src/features/advanced-chart/` and new backend code must be additive.
- Preserve the existing Markets workflow as the baseline regression target.
- No demo/archive/simulated provider may be enabled as a fallback in production. No hardcoded market values.
- No write-side trading/order functionality is in scope; this is a read-only analysis/charting workspace.

## 7. Verification plan

- Unit tests for candle normalisation, timestamp/price scaling, interval mapping, missing fields, OI classification and option-chain calculations.
- API tests for authentication, invalid symbols/exchanges/intervals, upstream timeout/errors and read-only behaviour.
- Frontend tests for chart lifecycle, symbol/interval switching, data refresh, stream reconnect/fallback and unmount cleanup.
- Build checks: frontend production build plus relevant backend market tests.
- Regression checks: existing Markets page renders and continues its original API/refresh behaviour; no gateway/auth/config changes.
- Evidence required before calling it complete: test command output, changed-file list, verified API payload examples with secrets redacted, and clear list of any remaining provider/licensing blockers.

## 8. Open implementation gates

1. **Reference licence:** obtain a separate commercial licence if source code/assets are to be copied or adapted for commercial use. This design assumes clean-room reimplementation unless permission is provided.
2. **Derivatives data:** verify m.Stock supports the required futures/option-chain fields and the current gateway can resolve the correct contracts and expiries.
3. **Streaming:** verify a real subscription stream rather than relying on a one-message WebSocket connectivity test.
4. **Chart library:** select the chart engine after dependency/licence review; do not add a dependency before this check.

## 9. Completion definition

The work is complete only when the Advanced Chart tab contains the full interactive charting and market-flow experience described above, driven by genuine provider data, with no fabricated values, and all existing Markets workflows pass regression checks. A static mockup, chart screenshot, cards-only dashboard, or unconnected demo is not completion.
