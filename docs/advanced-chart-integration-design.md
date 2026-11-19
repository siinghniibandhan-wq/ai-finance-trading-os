# Financial OS Market Analytics — Current Architecture

**Architecture baseline:** 19 November 2026  
**Repository:** `siinghniibandhan-wq/ai-finance-trading-os`  
**Status:** Updated to match the implemented source tree and approved REST-only scope.

## 1. Product workspaces and navigation

The Markets navigation has four workspaces. This is the current application structure, not a proposed future layout.

1. **Markets** — existing market overview in `frontend/src/App.jsx`. Preserve its current behaviour, state, endpoints and refresh lifecycle.
2. **Order Flow / Chart Flow** — whole-market and sector discovery. `App.jsx` mounts `frontend/src/features/order-flow/OrderFlowPage.jsx`, which renders `MarketFlowBoard.jsx`. Chart Flow is part of Order Flow; it is not a separate main navigation item.
3. **Advanced Chart** — individual-instrument historical OHLCV charting and technical analysis, implemented in `frontend/src/features/advanced-chart/AdvancedChartPage.jsx`.
4. **Options Hub** — separate derivatives workspace, implemented in `frontend/src/features/options-hub/OptionsHubPage.jsx`. It remains data-gated until a verified provider contract is connected.

Do not create a fifth Markets workspace or move Chart Flow into Advanced Chart. Do not replace the existing Markets or Advanced Chart workflows.

## 2. Runtime architecture

```
React application (frontend/src/App.jsx)
  |
  +-- Markets (existing MarketsPage)
  |
  +-- Order Flow / Chart Flow
  |     OrderFlowPage.jsx
  |       -> MarketFlowBoard.jsx
  |           -> authenticated apiFetch via advanced-chart/api.js
  |           -> GET /api/market-flow/
  |           -> GET /api/market-flow/?sector={key}
  |           -> GET /api/market-charts/ (selected instrument daily history)
  |
  +-- Advanced Chart
  |     AdvancedChartPage.jsx
  |       -> authenticated apiFetch via advanced-chart/api.js
  |       -> GET /api/market-search/
  |       -> GET /api/market-charts/
  |       -> GET /api/market-quote/
  |
  +-- Options Hub
        OptionsHubPage.jsx
          -> authenticated apiFetch via options-hub/api.js
          -> GET /api/options-hub/master and /api/options-hub/chain

FastAPI backend (backend/app/main.py; private routers behind the existing
authenticated-user dependency)
  |
  +-- options_hub.py
  |     -> m.Stock Gateway /options/master and /options/chain
  |     -> gateway-owned Script Master parsing and batched REST contract quotes
  |
  +-- market_flow.py
  |     +-- market_movers.py -> m.Stock Gateway /gainers-losers
  |     +-- market_indices.py -> m.Stock Gateway /quote (LTP + best-effort OHLC)
  |     +-- sector universe and selected-sector mover aggregation
  |
  +-- market_charts.py -> market_history.py
  |     +-- Gateway /instruments (instrument master)
  |     +-- Gateway /historical/{exchange}/{token}/{interval}
  |
  +-- market_quote.py -> market_price service -> Gateway quote
  |
  +-- market_search.py -> existing instrument search/master

m.Stock Gateway
  +-- Bearer token / provider authentication remains gateway-side
  +-- Financial OS shared-secret header remains backend-to-gateway
  +-- provider access tokens and secrets never enter the browser
```

All frontend requests use the existing `apiFetch` authentication/session path. Backend-to-gateway calls use the existing `MSTOCK_GATEWAY_URL` and `MSTOCK_GATEWAY_SECRET`. Do not add a parallel login mechanism, expose gateway credentials, or call m.Stock directly from the browser.

## 3. REST transport and refresh behaviour

- REST is the only market-data transport for this scope.
- No WebSocket, socket client, event stream, streaming worker, tick subscription or streaming cache may be added.
- Chart Flow market snapshot refreshes every 30 seconds while the page is visible.
- Selected-sector data refreshes every 60 seconds while the page is visible.
- The frontend labels these as REST snapshots. Retrieval time is not an exchange event timestamp.
- Advanced Chart uses authenticated REST history and quote snapshots. Existing Advanced Chart interval controls are preserved; this does not add intraday features to Chart Flow.
- Chart Flow historical stock analysis uses daily OHLCV only. Do not add intraday reconstruction or intraday Chart Flow panels.
- Requests must remain bounded, provider-rate-safe, cancellable/guarded on unmount, and honest about partial responses. The m.Stock Type A documentation currently specifies 1 data API request/second and 20 quote API requests/second; keep the shared mover-request pacing and do not assume the data-API allowance applies to quote endpoints.

## 4. Chart Flow data model and current implementation

### Market-wide flow

`backend/app/routes/market_flow.py` requests provider-ranked NSE and BSE cash-market gainers and losers using the Type A Top Gainers/Losers API with the provider's ALL security classification. The frontend builds a zero-centred distribution, bullish/bearish paths, filters, volume participation and instrument selection from the returned rows.

**Important data boundary:** the provider mover endpoint returns ranked movers, not every unchanged listing. The API response now labels this explicitly as `provider_ranked_sample`, sets `market_summary.sample_only=true` and `breadth_complete=false`, and leaves unchanged count null. Current bullish/bearish counts and volume summaries describe only returned rows. They must never be labelled as full-exchange breadth, market-wide total volume or total listed-market participation.

### Sector flow

The backend maintains 17 provider-documented NSE sector classifications and corresponding index symbols. It exposes:

- the sector universe in the market snapshot;
- sector index snapshots with LTP and, when returned by the gateway's OHLC-enriched quote, previous close and calculated daily change;
- selected-sector provider-ranked gainers and losers;
- a sector index node and constituent-mover flow in the frontend.

The index quote path uses the gateway's `/quote?symbol={EXCHANGE}:{SYMBOL}` endpoint because the current gateway `/index-quote` endpoint proxies LTP only. The `/quote` endpoint supplements LTP with Type A OHLC on a best-effort basis. The backend derives daily change only from the provider's OHLC close; missing OHLC remains unavailable.

**Important data boundary:** the sector mover endpoint is a ranked sample, not a complete sector constituent feed. The 17-sector diagram can show only sector index performance actually returned by the provider. Sector breadth, full constituent returns and sector rotation history are not available from this data contract.

### Historical stock chart

Chart Flow requests daily OHLCV for the selected instrument through `GET /api/market-charts/`. Candles are validated before the UI derives relative price performance and candle geometry. Missing volume remains missing. This is an individual stock's daily history, not historical market-wide breadth or historical sector membership.

## 5. Advanced Chart

The current Advanced Chart implementation includes:

- Candlestick, OHLC bar, line, area and Heikin-Ashi chart modes.
- Historical OHLCV through the authenticated Market Charts route.
- Volume histogram and REST quote/LTP marker.
- SMA 20, EMA 20, Bollinger Bands (20, 2) and VWAP overlays.
- RSI 14 and MACD (12, 26, 9) indicator pane.
- Existing symbol selection, search, scanner handoff and chart interactions.

Indicators are derived from loaded source candles. VWAP is an intraday benchmark in the existing Advanced Chart implementation; it must not be repurposed as a Chart Flow daily historical metric. Preserve current Advanced Chart behaviour during this work.

## 6. Options and futures capability boundary

The Options Hub now has an additive, authenticated REST adapter and an independently authored strike-chain interface. It requests the gateway routes `/options/master` and `/options/chain`, which are present in the saved options-enabled gateway source variant. This repository branch does not prove that those routes are deployed on the active AWS gateway; a 404 is surfaced as an explicit gateway-unavailable state. The master/data provider APIs are documented but their runtime availability and account entitlement remain unverified.

The current gateway options-chain variant builds CE/PE contracts from the provider Script Master and requests contract LTP/volume in batches. OI is passed through only if the quote response supplies it. The Financial OS model calculates PCR, Max Pain and the mirrored strike OI chart only when every displayed strike has both CE and PE contracts with valid non-negative OI. Otherwise those analytics are withheld.

The following must remain unavailable until the real REST payload supplies and verifies them:

- bid/ask and quote fields not present in the gateway response;
- OI change and historical OI observations;
- futures price/OI observations;
- long build-up, short build-up, short covering and long unwinding;
- OI concentration and writer positioning;
- OI-derived support/resistance;
- historical OI series, IV and Greeks.

A single OI snapshot cannot be presented as historical OI change. Equity volume cannot substitute for futures OI. Spot prices cannot substitute for futures prices. Do not add placeholder charts or synthetic values to make these screens appear active.

The current adapter expects the saved gateway options-enabled route contract. Before describing the Options Hub as live, verify the exact deployed gateway source/version, authenticated upstream response, account entitlement, field definitions, units, expiry/token mapping, quote coverage, rate limits and failure behaviour. Any gateway deployment/change is a separate controlled change; do not change live secrets or systemd configuration as part of this repository-only branch.

## 7. Capabilities not provided by current REST contracts

These are provider/data-contract gaps, not frontend components that can safely be fabricated:

| Capability | Current boundary | Required evidence before implementation |
|---|---|---|
| Full NSE/BSE advance-decline breadth | Top-mover lists are not a complete instrument universe; the response is explicitly marked `provider_ranked_sample` | Complete exchange universe plus current and previous-close observations, with verified quote coverage |
| Full sector constituent breadth | Selected-sector endpoint returns ranked movers | Complete, current sector membership and quote coverage |
| Historical market-wide breadth | No persisted full-universe daily snapshots | Reliable complete daily observations and an approved persistence/retention design |
| Historical sector rotation | Current sector index snapshot only | Verified index instrument tokens and daily historical index OHLC |
| Delivery statistics | Not in current quote/mover contract | Documented provider REST endpoint and field contract |
| Futures OI history | Not established by current history route | Verified futures contract mapping and historical OI source |
| Option chain LTP/volume | Financial OS REST adapter now calls gateway options routes; deployment and provider coverage unverified | Authenticated live gateway response and quote coverage |
| Options OI/PCR/Max Pain | Calculations implemented only for complete two-sided provider OI; current gateway may return null OI | Authenticated OI fields for every CE/PE contract with verified units |
| Options IV/Greeks/bid-ask/OI change | Not supplied by the current saved gateway quote adapter | Documented provider REST fields and verified response |
| Historical OI change | No historical OI observations | Time-series source or controlled snapshot collection |
| Full-market turnover | Mover rows are a sample | Complete exchange-level turnover source |

Do not substitute unrelated data to fill these gaps. If a provider endpoint is unavailable, show an explicit unavailable state and record the blocker.

## 8. Security, licensing and preservation

- Preserve existing Bearer authentication, private backend route dependency, gateway shared-secret validation and provider token handling.
- Preserve broker-order APIs and safeguards; this is a read-only analytics scope.
- No database writes are made by the current Chart Flow snapshot route.
- Do not change AWS, EC2, systemd, gateway secrets, Amplify, deployment automation or database migration behaviour in this branch.
- The MrChartist reference repository is PolyForm Noncommercial 1.0.0. Financial OS must remain a clean-room, independently authored implementation unless separate commercial permission is obtained. Do not copy source code, assets, styling or logos.

## 9. Verification and release gates

Before merge:

1. Run focused backend market-index and market-flow tests.
2. Run frontend Order Flow and Advanced Chart tests.
3. Run backend regression tests and frontend production build using repository scripts.
4. Verify the Market workspace and existing Advanced Chart workflows are preserved.
5. Verify sector-index requests use the OHLC-enriched REST quote path and that missing OHLC stays unavailable.
6. Confirm CI on the pull request.
7. Perform an authenticated production smoke test separately before describing sector indices or derivatives as live. Repository tests do not prove AWS gateway availability or m.Stock account entitlement.

This document describes the architecture in the current source tree. It supersedes the older proposed navigation and streaming/intraday requirements recorded in earlier drafts.
