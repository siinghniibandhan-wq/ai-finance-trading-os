# Financial OS Order Flow — Design Specification

**Date:** 2026-11-19  
**Repository:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Target branch:** `feature/market-analytics-rest-chart-suite`  
**Phase:** 1 of the approved sequential programme (Order Flow → Options Hub → integration)

## Goal

Deliver a full, interactive Order Flow workspace inside the existing Markets section. It will provide market-wide directional discovery, instrument-level flow context, and futures analytics when verified provider data exists, while keeping Advanced Chart as the dedicated instrument price-analysis workspace.

## Product structure

The Markets section will expose four sibling workspaces:
1. **Market** — preserve the existing Markets page and its current behaviour.
2. **Order Flow** — market-wide discovery and directional/derivatives flow analysis.
3. **Advanced Chart** — dedicated detailed price-chart workspace.
4. **Options Hub** — a later sequential phase for option-chain and options strategy analysis.

These are separate workspaces within the existing Markets area, not separate applications. Order Flow and Advanced Chart will share instrument identity and chart navigation, but their primary purposes remain distinct.

## Order Flow scope

### Included

- Market-wide bullish and bearish distribution using only provider-returned, validated instruments.
- Directional ranking and drill-down to the selected instrument.
- Index snapshots and sector/index views only for symbols and values supported by verified provider contracts.
- Futures build-up classification (long build-up, short build-up, short covering, long unwinding) only when comparable futures price and open-interest observations for the same contract and time window are available.
- Instrument-level context, with navigation into Advanced Chart.
- Full responsive visual workspace: flow distribution visualisation, sector/index panels where supported, sortable/rankable instrument lists, instrument detail, clear source and freshness indicators.
- REST refresh with bounded requests, request de-duplication, visibility-aware refresh, cancellation/cleanup, and explicit stale/partial/error states.

### Explicitly excluded

- WebSockets, raw sockets, EventSource, streaming workers, market-data subscriptions, or any continuous streaming transport.
- Simulated/demo prices or fabricated candles, OI, breadth, sector constituents, PCR, or support/resistance.
- Treating a bounded gainers/losers response as full-market breadth or capital/traded-value flow.
- Inferring futures OI from equity volume or substituting spot values for futures contracts.
- Replacing or refactoring the existing Market page or changing its established API, state, refresh, or workflow.
- AWS deployment, gateway runtime configuration, credentials, secrets, or authentication changes.
- Copying MrChartist source code, assets, branding, or other protected implementation. The references guide independently authored functionality and visual hierarchy only.

## Existing repository context

- Frontend: React 18 + Vite under `frontend/`; main navigation and view selection are in `frontend/src/App.jsx`.
- Existing Markets navigation entries are Market and Advanced Chart.
- Advanced Chart implementation exists under `frontend/src/features/advanced-chart/`, using Lightweight Charts 5.0.8 and the shared authenticated `apiFetch` client.
- Existing REST market endpoints include `/api/market-overview/`, `/api/market-movers/`, `/api/market-search/`, `/api/market-quote/`, and `/api/market-charts/`.
- Existing market overview combines configured index snapshots and bounded gainers/losers responses. Its response is explicitly partial when one source fails.
- Current frontend focused test commands include `npm run test:market`, `npm run test:advanced-chart`, and `npm run build` from `frontend/`.
- Existing backend test suite uses pytest; focused market tests are under `backend/tests/test_market_*.py`.

## Provider capability boundary

The current integrated m.Stock Type A REST contract supports quote/LTP, historical candles, script master, gainers/losers and index quote, subject to provider availability and runtime configuration. The integrated contract does not currently verify full-market breadth, sector constituents, futures OI history, or historical OI time series.

Therefore:
- Current supported data may drive market-mover directional distribution and supported index snapshots.
- Sector views must show only verified supported index series; they must not imply sector constituent breadth without a verified constituent universe.
- Futures build-up panels must expose an unavailable/provider-not-connected state until a verified REST source returns both futures price and OI for the same contract and observation window.
- A future provider adapter may be added only after its REST endpoint, authentication model, instrument identifiers, timestamps, units/scaling, rate limits, and response schema have been verified. It must reuse existing Financial OS auth boundaries and must not expose provider secrets to the browser.

## Architecture

- Keep Order Flow isolated under `frontend/src/features/order-flow/` with focused page, components, styles, data adapter, pure model functions, and tests.
- Register Order Flow in the existing Markets navigation/view routing with the smallest possible change to `frontend/src/App.jsx`.
- Use the existing authenticated `apiFetch` client for browser requests. Reuse existing backend market routes and services where their contracts are sufficient.
- Add backend aggregation/routes only where existing response contracts cannot safely express the required view; keep provider-specific parsing server-side and read-only.
- Share instrument selection/navigation through explicit instrument identity (`symbol`, `exchange`, and provider instrument identity when available). Opening a selected instrument in Advanced Chart must use its existing supported navigation contract or a small explicit callback contract.
- Keep Advanced Chart's detailed price plotting and indicator controls in its own workspace; Order Flow may show compact context charts only where they improve flow analysis.

## Data contract requirements

Every Order Flow response used for analytics must identify:
- data source/provider;
- instrument identity and exchange/segment where applicable;
- observation or exchange timestamp when supplied by provider;
- server retrieval timestamp separately;
- freshness/age and partial/error status;
- explicit field availability.

Missing values remain null/unavailable. Retrieval time must never be presented as exchange time. Derived classifications must record the exact inputs and calculation rule and must not run when required inputs are missing or incomparable.

## Visual and interaction requirements

- Dense, professional trading-workspace layout inspired by the reference products' information hierarchy, independently implemented.
- Flow distribution is a true data visualisation, not decorative lines or static mock data.
- User can filter supported exchange/segment or direction, sort available instruments, search within returned rows, select an instrument, and open it in Advanced Chart.
- Loading, empty, stale, partial, provider unavailable, and request error states are visually distinct.
- Desktop-first analytical density with responsive layouts for smaller screens; charts must resize with their containers and remain usable.
- Keyboard-operable controls and accessible labels for primary interactions.

## Error and refresh behaviour

- REST requests are bounded and deduplicated; no overlapping refresh for the same view.
- Refresh only while the workspace is visible; cancel or ignore stale responses after navigation/unmount.
- A failed source must not erase successful independent source results.
- Preserve last successful data only with a visible stale indicator and its original retrieval timestamp; never relabel it as current.
- HTTP authentication failures use the existing shared session behaviour; no parallel auth mechanism is introduced.
- No automatic fallback to simulated or cached demo data.

## Testing and acceptance

1. Pure model tests cover provider-row normalization, unsupported/missing fields, direction grouping, sorting, freshness, partial sources, and futures classification eligibility.
2. API contract tests cover valid, malformed, empty, partial, unavailable, and failed provider responses without live provider credentials.
3. UI tests cover filters, search, selection, navigation to Advanced Chart, responsive states, and loading/empty/error/stale presentation.
4. REST-only regression checks ensure no WebSocket, socket.io, EventSource, WebSocket constructor, streaming worker, or market-data subscription transport is introduced by this feature.
5. Run focused frontend tests, backend market tests, full frontend production build, and the repository's relevant backend regression suite.
6. Verify the existing Market page and Advanced Chart workflows remain available and unchanged in behaviour.

**Phase 1 exit condition:** Order Flow is a complete interactive market-discovery workspace using verified REST data, with real flow visualisation, supported index/sector context, honest provider-capability states, working instrument hand-off to Advanced Chart, responsive charts, and passing regression checks. Unsupported futures/OI capabilities are not represented as working until a verified REST provider contract is integrated.

## Later sequential phases

- **Phase 2 — Options Hub:** its own reviewed specification and implementation plan covering option-chain contracts, CE/PE OI, PCR, Max Pain, IV, Greeks, GEX, strategy payoff and backtesting. It must first verify a provider REST contract and authentication compatibility; no fabricated derivatives data.
- **Phase 3 — Integration:** shared navigation/instrument context, common chart conventions, cross-workspace hand-off, and combined regression verification.
