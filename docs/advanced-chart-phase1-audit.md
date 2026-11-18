# Advanced Chart — Phase 1 Audit and Acceptance Record

**Target:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Implementation branch:** `feature/advanced-chart-phase-1`  
**Reference:** `MrChartist/order-flow`  
**Architecture source:** [advanced-chart-integration-design.md](./advanced-chart-integration-design.md)

## Agreed Phase 1 runtime decision

Phase 1 uses the existing authenticated Financial OS REST APIs. The selected instrument's latest quote is refreshed every **10 seconds** while the page is visible. No WebSocket connection, continuous tick stream, new gateway worker, or streaming protocol is part of this phase.

Historical candles remain the provider's OHLCV history. A quote snapshot updates the chart's LTP price line; it must not be misrepresented as a new candle or used to fabricate candle OHLC. Quote retrieval time is not an exchange timestamp.

## Reference project audit

The reference repository is a complete market-flow workspace, not just a candle chart. Its major functional areas were reviewed:

| Reference area / files | Behaviour and data dependency |
|---|---|
| `MarketFlowPage.tsx`, `FlowBoard.tsx` | Workspace, NIFTY 50 / All F&O universe, responsive diagram/desktop/tablet/phone layouts, panel selection and focus controller |
| `FlowChart.tsx`, `FlowDiagram.tsx`, `diagramModel.ts`, `flowChartModel.ts` | Per-underlying futures price paths, zero baseline, bullish/bearish distribution, ranking, chart geometry and line interactions |
| `FlowSide.tsx`, `FlowParts.tsx`, `FlowSectors.tsx` | Ranked symbol tiles, build-up markers, sector medians and interactive focus |
| `FlowPopup.tsx`, `flowFocus.ts`, `FlowStatus.tsx` | Pinned/hovered instrument details, support/resistance/option levels, source and freshness status |
| `marketFlowModel.ts`, `useMarketFlow.ts`, `feed.ts`, `nifty50.ts` | Flow calculations, instrument universe, one-minute market-file polling, futures retrieval and freshness/session handling |
| `options-scanner/contractScanModel.ts`, `futuresModel.ts` | Per-strike CE/PE option-chain model, OI changes, futures price/OI windows and build-up classification |
| `server/marketFile.mjs`, `server/providers/types.mjs` | Market-file schema and provider contract for option chains and futures |
| `MarketFlowPage.test.tsx`, `MarketFlowBoard.test.tsx`, model tests | UI, focus, layout and calculation regression coverage |
| `package.json`, `LICENSE`, `README.md`, `PROVIDERS.md` | Dependencies, provider options, operating model and licensing |

The reference's own feed is HTTP/REST based: the market file is polled every minute after initial load; futures are fetched in bounded batches and refreshed on a slower cadence. The reference does not require a continuous browser WebSocket for its board.

**Licensing:** the reference is under PolyForm Noncommercial 1.0.0. Financial OS must remain a clean-room, independently authored implementation. Do not copy its source, assets, styling, logos or other copyrightable implementation. Commercial reuse of the reference code requires a separate licence.

## Financial OS data capability matrix

| Capability | Existing Financial OS evidence | Phase 1 decision |
|---|---|---|
| Authenticated browser requests | `frontend/src/api.js` exposes `apiFetch`; private routers are registered behind `auth.get_current_user` in `backend/app/main.py` | Reuse unchanged |
| Instrument search | `GET /api/market-search/`; current search supports NSE/BSE cash Stocks and returns instrument metadata | Reuse; expose ALL/NSE/BSE filter in Advanced Chart |
| Historical OHLCV | `GET /api/market-charts/` delegates to `market_history.py`, resolves instrument token from the gateway master, and returns timestamp/OHLCV candles | Reuse; no synthetic candle fallback |
| Supported history intervals | `minute`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`, `day` | Expose the supported intervals |
| Quote / LTP | `GET /api/market-quote/` uses `market_price.py` and returns last price, provider details, retrieval time and cache metadata | Reuse; poll every 10 seconds and draw LTP line |
| Exchange timestamp | Current quote route explicitly returns `provider_market_timestamp: null` | Display retrieval time only; never relabel it as exchange time |
| Index snapshots | `GET /api/market-indices/` requests NIFTY 50, SENSEX, NIFTY BANK and INDIA VIX | Real index snapshots exist; not a full market-flow universe |
| Gainers / losers | `GET /api/market-movers/` and `market_overview.py` expose provider mover rows | Real mover samples exist; the overview's unchanged count is hard-coded to zero and must not be used as complete market breadth |
| Sector distribution | No verified complete sector constituent + price time-series API found in the inspected Financial OS routes | Do not render a sector-flow visualisation as live |
| Futures prices and historical OI | Existing chart/history path accepts NFO/BFO, but the inspected Financial OS quote/search path does not establish a verified futures/OI time-series contract | Provider capability gap; do not infer from cash prices or volume |
| Per-strike option chain / CE-PE OI | No verified Financial OS option-chain route or provider contract found in the inspected route set | Provider capability gap; no fabricated option profiles, PCR or writer positioning |
| Historical OI / OI change | No verified source-backed time series found | Do not derive historical OI from a current snapshot |
| Continuous WebSocket | Not needed for this phase and not part of the agreed runtime architecture | Not implemented; 10-second REST quote polling is the agreed approach |

## Phase 1 implementation acceptance

- [x] Isolated Advanced Chart navigation item under Markets.
- [x] Existing Markets item/component/state/API/refresh workflow retained; only the additional navigation registration is made in `App.jsx`.
- [x] Authenticated `apiFetch` used for all protected market requests.
- [x] Provider instrument search and NSE/BSE exchange filtering.
- [x] Historical OHLCV candle normalization, sorting, validation and duplicate timestamp handling.
- [x] Interactive candlestick chart with crosshair, time/price scales, pan/zoom, responsive resizing and volume pane.
- [x] Interval and date-range controls.
- [x] SMA 20 and EMA 20 overlay controls.
- [x] 10-second REST quote polling with visibility handling and overlap prevention.
- [x] LTP is displayed as a chart price line; quote snapshots do not mutate or fabricate OHLC candles.
- [x] Provider/source, quote retrieval time and gateway cache age are disclosed.
- [x] No demo feed, simulated prices, fake candles or fabricated OI are used.
- [x] No gateway secret, Bearer auth, backend gateway, AWS/systemd or deployment configuration changes.
- [x] Final PR CI regression run on commit `aefe161e9a62036969249f425c287db4370fd275`: frontend tests/build, backend regression tests, dependency audits and repository secret scan all passed.
- [x] App navigation diff reviewed: only the Advanced Chart import, Markets submenu item, valid-page entry and isolated render branch were added; the existing Markets component branch remains unchanged.
- [ ] Authenticated production runtime smoke test against real provider data (not run in this code-only work; no environment access was requested or used).

## Phase 1 visualisation boundary

The reference's full market-flow board depends on a complete F&O universe, futures price/OI series, option-chain OI by strike, and sector membership/time series. Those contracts are not established by the current Financial OS routes audited above. The current index and top-mover endpoints are not a substitute for those datasets. Therefore Phase 1 must not display a counterfeit market-flow board, synthetic breadth, fake futures build-up, fabricated support/resistance or option OI.

The full market-wide flow and advanced derivatives parity remain Phase 2 work under the architecture specification, gated on verified m.Stock/provider contracts. This is a data-integrity boundary, not a chart-library limitation.

## Verification evidence

The previously recorded CI run for commit `a3a09c4836f34a178344f542f15cbc34dcc11f23` passed the backend regression suite, frontend production build, existing notice/sidebar/Market Overview regressions, Advanced Chart candle normalization tests, dependency audits and secret scan.

Additional Phase 1 changes on this branch harden provider timestamp parsing, preserve valid OHLC rows when volume is unavailable, and align historical instrument resolution with the provider header aliases already supported by Market Search. Regression tests cover these cases.

Code verification for PR #216, head commit 87f8c8c2b001af7186b29faac0ee3cd58a304318:
- Frontend production build: PASS (workflow run 44409927316).
- Financial OS CI: PASS (workflow run 44409927419).
- Backend regression suite: 380 passed, 2 skipped.
- Frontend Advanced Chart candle normalization tests: PASS.
- Repository secret scan and dependency audits: PASS.

The authenticated production runtime smoke test was intentionally not run in this code-only work. It is recorded separately from repository-code completion and remains unverified until an authorized runtime check is requested.

**No merge is authorised by this audit record.**
