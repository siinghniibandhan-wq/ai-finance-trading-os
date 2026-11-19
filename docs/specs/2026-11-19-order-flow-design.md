# Financial OS — Chart Flow Design Specification

**Date:** 2026-11-19  
**Repository:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Implementation branch:** `feature/chart-flow-rest-completion`  
**Status:** Incremental implementation; not release-ready.

## Goal

Complete the existing Chart Flow workspace as a distinct, modern, interconnected market-flow analysis experience. The primary visual reference is the interaction hierarchy in the Mr. Chartist repository; all Financial OS implementation code, visuals and assets must be independently authored.

Chart Flow is not a duplicate of Market and is not a replacement for Advanced Chart.

## Protected workspaces

1. **Market** — preserve existing page, APIs, state, refresh and workflows.
2. **Chart Flow** — build the connected market-to-sector-to-stock visual analysis workspace.
3. **Advanced Chart** — preserve detailed charting, indicators, OHLC and existing instrument handoff.
4. **Options Hub** — separate workspace; leave its current implementation untouched. Option Chain and Open Interest may be considered independently later.

Do not change authentication, broker order APIs, gateway secrets, trading workflows or live AWS configuration.

## Chart Flow experience

The visual hierarchy should show how information moves through connected stages:

1. Market direction and provider-returned gainers/losers.
2. Bullish/bearish price distribution and index context.
3. Sector selection and sector-filtered mover distribution.
4. Selected sector's strongest/weakest provider-ranked instruments.
5. Selected stock's price, volume and historical OHLCV context.
6. Explicit handoff to the existing Advanced Chart for full technical analysis.

Selecting a sector must update the sector distribution and its mover lists. Selecting an instrument must update instrument detail and its historical context. The design must be chart-led, readable, responsive and interactive, not a stack of generic data cards.

## REST-only integration and shared APIs

Architecture:

`Chart Flow UI → existing authenticated Financial OS FastAPI routes → existing m.Stock Gateway → m.Stock REST APIs`

- REST only. No WebSockets, Socket.IO, EventSource, streaming workers or continuous subscriptions.
- Reuse the existing `/api/market-flow/` route. An optional `sector` query selects a provider sector; do not create separate sector-list or sector-detail routes.
- The default `/api/market-flow/` response supplies the shared market snapshot and sector-universe metadata.
- Chart Flow requests `/api/market-flow/?include_sector_indices=true` to load sector index quotes through the same route. Results are briefly cached server-side.
- A selected sector uses `/api/market-flow/?sector=<key>` and returns its actual provider-ranked movers and the selected sector index quote.
- The existing Gateway `/index-quote` contract is enriched best-effort with the existing m.Stock Type A OHLC API. Financial OS derives index daily change only from the provider's OHLC `close` (previous close) and LTP. If OHLC is not available for an index, its percentage change remains unavailable.
- Reuse the existing authenticated `apiFetch` adapter in `frontend/src/features/advanced-chart/api.js`; do not create duplicate browser API clients.
- Reuse the existing `/api/market-charts/` historical OHLCV route for selected-stock history. Do not create a duplicate historical endpoint.
- Reuse existing index and quote services where their provider contracts are sufficient.
- Keep provider credentials and response parsing server-side.
- Respect m.Stock's documented data API rate limit of one request per second. Requests must be bounded, deduplicated where appropriate, and cached briefly when safe.

## Verified m.Stock sector mover contract

m.Stock Type A Top Gainers/Losers supports the `SecurityIdCode` sector/index universe. The documented NSE values include:

| Code | Provider universe |
|---:|---|
| 9 | NIFTY AUTO |
| 10 | NIFTY PVT BANK |
| 20 | NIFTY FMCG |
| 21 | NIFTY IT |
| 22 | NIFTY MEDIA |
| 23 | NIFTY METAL |
| 24 | NIFTY PHARMA |
| 25 | NIFTY PSU BANK |
| 26 | NIFTY REALTY |
| 33 | NIFTY ENERGY |
| 34 | NIFTY INFRA |
| 35 | NIFTY MNC |
| 37 | NIFTY SERV SECTOR |
| 59 | NIFTY CONSUMER DURABLES |
| 60 | NIFTY FINANCIAL SERVICES |
| 61 | NIFTY OIL AND GAS |
| 62 | NIFTY HEALTHCARE INDEX |

This endpoint returns ranked gainers and losers within the selected provider universe. It does **not** return every sector constituent or establish full sector breadth. Sector index percentage performance is shown only when the existing Gateway returns provider OHLC previous-close data; an index LTP alone is never presented as percentage performance.

## Data and analytical boundaries

- Use only provider-returned prices, percentage changes, volumes, index quotes and historical candles.
- Current mover distributions describe the provider-returned rows, not all listed securities.
- Full-market advance/decline breadth is unavailable from top-gainer/loser lists alone.
- Full sector constituent breadth is unavailable from ranked mover lists alone.
- Do not average a truncated gainer/loser sample and label it as sector performance.
- Do not infer market-wide traded value or participation from a subset of mover volumes.
- Historical stock performance may be calculated from returned daily OHLCV candles; identify the base observation and calculation clearly.
- Missing fields remain unavailable. No synthetic, demo, simulated or fabricated market data.
- Keep provider retrieval time separate from provider observation time.
- Intraday analysis is not blocked by missing Option Chain or Open Interest. Its exact interval coverage must follow verified m.Stock REST availability and the separately confirmed Chart Flow time-range scope.

## Visual and interaction requirements

- Interconnected directional flow diagram.
- Market mover distribution around a zero reference.
- Sector selector with actual sector-filtered mover distribution.
- Sector index level where returned.
- Gainer/loser lists within the selected sector.
- Search, exchange and direction filters; sorting by supported fields.
- Selected-stock detail with price change and actual volume.
- Compact historical price/volume chart from existing daily OHLCV data.
- Clear Advanced Chart handoff.
- Keyboard-operable controls and accessible labels.
- Distinct loading, empty, partial, stale and provider-error states.
- Responsive analytical layout.

## Development and acceptance

1. Inspect actual Financial OS source and Mr. Chartist reference implementation before structural changes.
2. Reuse existing routes, services, instrument identities and adapters before adding new code.
3. Add new backend routes only when no existing route can express the required operation.
4. Add tests before model/backend changes; test valid, missing, partial and failed provider responses.
5. Run focused Chart Flow model tests, backend market-flow tests, full backend suite, full frontend tests, production build and workspace regression checks.
6. Verify Market and Advanced Chart remain operational and Options Hub remains untouched.
7. Keep live AWS Gateway unchanged until code review and all regression checks pass.

## Current known limitations

- m.Stock ranked sector movers and current sector index quote are supported by documented provider identifiers and the existing Gateway contracts.
- Complete sector constituent universe, full sector breadth and percentage sector-index performance are not established by the current integrated response contracts.
- Full-market advance/decline breadth is not established by the current gainers/losers response.
- Do not represent these as completed until a verified provider REST source is integrated.

**Release condition:** Chart Flow is accepted only when its connected market → sector → stock experience is working with genuine REST data, all supported visualisations and interactions pass tests, protected workspaces remain operational, and unsupported metrics are clearly identified rather than fabricated.
