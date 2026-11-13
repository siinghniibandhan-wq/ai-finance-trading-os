# Full Market Order Flow Terminal — Design

**Status:** Proposed implementation design, approved direction from the user; awaiting review of this written specification before implementation.

## Goal

Replace the card-led Market Intelligence page with a complete, interactive market order-flow terminal integrated into the existing Financial OS, preserving existing market, broker, order-placement, authentication, and navigation behavior.

## Product scope

The terminal is a set of connected workspaces, not a collection of summary cards:

1. **Market Flow (default landing view):** animated bullish/bearish flow visualization with directional movement, flow magnitude, filtering, hover/highlight, selection, and linked stock details.
2. **Flow Board:** market-wide sortable/filterable instrument positioning board with price, price change, futures open-interest change, classification, and data freshness.
3. **Stock Explorer:** selected-instrument detail view, linked from the flow diagram and board, with price/OI context, conviction checks, and relevant charts.
4. **Futures:** long build-up, short build-up, short covering, and long unwinding classifications using provider-supplied price/OI observations.
5. **Options:** option-chain view, PCR, call/put OI distribution, highest-OI levels, and derived support/resistance when sufficient provider data exists.
6. **Sector Flow:** sector rotation and constituent breadth/strength visualization.
7. **Charts & Replay:** intraday charting and historical/replay workspace, gated by actual historical data availability.
8. **Market Monitor:** provider connection state, last successful tick/snapshot, reconnect/error information, and explicit feed coverage.

## UX and interaction

- Market Flow is the default view. It is the primary visual workspace, not an overview of metric cards.
- Selecting or hovering an instrument highlights its flow path and synchronizes selection with Flow Board and Stock Explorer.
- Filters and sorting apply to the underlying instrument set and are visible in the active workspace.
- Instrument details are contextual and can be opened without losing the current flow/board context.
- Desktop receives a dense terminal layout with persistent workspace navigation and multi-panel content. Smaller screens receive a responsive stacked layout without hiding core controls.
- Existing global theme tokens and theme switching remain authoritative; no page-local palette is introduced.
- Existing market overview snapshot, refresh behavior, and error messaging are retained where they remain useful.

## Architecture and data flow

- Keep the existing React/Vite frontend and FastAPI backend conventions.
- Build focused frontend components for the flow visualization, board, instrument detail, options, sectors, charts/replay, and feed monitor; keep shared selection/filter state in a narrowly scoped Market Intelligence workspace boundary.
- Continue using the existing authenticated read-only market analysis API for normalized futures/options/sector calculations.
- Audit the existing m.Stock Flask gateway and Type A stream worker before wiring live streaming. Add an explicit adapter boundary rather than coupling UI components to provider packet formats.
- Normalize provider observations into a documented market-data contract with instrument identity, exchange, timestamps, price fields, OI fields, option-chain rows, sector membership, and source/freshness metadata.
- The UI must distinguish live, delayed, snapshot, stale, partial, disconnected, and unavailable data. No generated/demo values may be presented as live.
- Historical charts and replay are enabled only where an actual historical source exists; missing history is clearly unavailable rather than synthesized.
- Keep all order execution and broker mutation paths outside this feature. The terminal is read-only; it must not submit, modify, cancel, or otherwise affect orders.

## Data integrity and failure behavior

- Missing provider fields remain unavailable; calculations requiring absent fields are not displayed as valid results.
- Stale observations retain their original timestamp and show a stale state.
- Partial provider responses may render available sections while identifying missing coverage.
- Stream disconnects do not erase the last observation silently; show its timestamp and disconnected/stale state.
- Invalid or malformed provider packets are rejected at the adapter boundary and surfaced through feed diagnostics without crashing the workspace.
- No credentials, broker tokens, or private provider configuration are exposed to the browser.

## Compatibility constraints

- Do not delete or alter existing forms, state, API calls, buttons, navigation, authentication, broker connections, or order-placement workflows outside the Market Intelligence surface.
- Preserve the existing market overview API and its current snapshot behavior unless a separately reviewed change is required.
- Do not introduce Vercel deployment configuration. Hosting remains AWS Amplify as already configured by the project.
- Do not change production, deploy, run migrations, or modify AWS/Amplify settings as part of this work.
- Work on `feature/full-market-order-flow-terminal`; deliver through a reviewable PR. Do not merge without separate approval.
- The reference project is used to understand product behavior and interaction patterns. Implementation must respect the source repository's PolyForm Noncommercial License 1.0.0. Do not copy its source code, assets, or protected expression unless the intended use is confirmed to be permitted. Reimplement the described capabilities using the existing platform architecture and original implementation.

## Delivery sequence

The overall product is decomposed into independently reviewable workstreams:

1. **Terminal shell and Market Flow + Flow Board:** replace the card-led page with the dense interactive flow workspace, instrument selection/highlighting, filters, and board; initially use only existing provider-backed snapshot data and clearly label unavailable F&O fields.
2. **Live normalized market-data integration:** connect the existing m.Stock Type A worker through the existing gateway using explicit lifecycle, subscription, cache, freshness, and reconnect boundaries; verify against safe test fixtures and a non-production provider connection only when credentials/environment are available.
3. **Futures and options workspaces:** connect actual futures/OI and option-chain inputs to existing calculation services; expose PCR, OI distribution, build-up classifications, conviction and support/resistance with source timestamps.
4. **Sector Flow, charts, historical archive and replay:** implement only to the extent supported by real source data and documented retention; do not simulate unavailable historical data.
5. **Hardening and release review:** responsive desktop/mobile checks, accessibility, performance, regression tests, docs, CI, and PR review. No production deployment or merge without separate approval.

## Testing strategy

- Discover and use the repository's existing frontend command: `cd frontend && npm test`; production build: `cd frontend && npm run build`.
- Add focused frontend tests for flow filtering, selection synchronization, missing/stale data states, and responsive navigation behavior using the test conventions already present in `frontend/tests`.
- Add backend tests for normalized provider observations, malformed/stale packets, stream lifecycle/reconnect behavior, and read-only guarantees.
- Run the existing backend regression test command identified from repository CI and project docs before PR readiness.
- Preserve existing market overview tests and broker/order regression coverage.
- Use deterministic fixtures only in tests; verify no fixture data is presented as live.

## Open integration dependencies

- The actual gateway lifecycle and current stream-worker integration seam must be confirmed from repository code before implementing the live adapter.
- Live futures and options coverage depends on the m.Stock account's subscribed instruments and the provider's actual payloads; do not assume that the current Type A quote/depth packet includes a complete F&O chain.
- Historical chart/replay availability depends on an existing data store or provider history API; this must be confirmed before enabling those workspaces.
- Any provider credentials or non-production connection setup must be supplied through existing secure backend configuration; never request or expose secrets in frontend code.
