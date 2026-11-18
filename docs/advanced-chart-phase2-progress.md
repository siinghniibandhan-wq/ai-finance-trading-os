# Advanced Chart Phase 2 — implementation status

Branch: `feature/market-flow-chart-suite-stage-1`  
PR: #219 (draft; not merged)

## Implemented in this branch

- Isolated REST-backed Gainer and Loser Scanner views using the authenticated `GET /api/market-movers/` endpoint.
- Provider-row validation for symbol, NSE/BSE exchange, positive LTP and percentage change; scanner direction is checked against the provider's percentage change.
- Search/filter/ranked percentage-move chart, reported-volume summary and bounded 30-second refresh while the view is visible.
- Scanner instrument selection opens the existing Advanced Chart.
- Price chart modes: Candlestick, OHLC Bar, Line, Area and Heikin-Ashi (derived from provider OHLC).
- Technical overlays: SMA 20, EMA 20, Bollinger Bands (20, 2) and VWAP (only when all loaded candles have valid positive volume).
- Separate indicator pane: RSI 14 and MACD (12, 26, 9), calculated from loaded provider closes.
- Existing Advanced Chart data path continues to use authenticated REST history and quote routes. The original Markets tab is not edited.

## Provider-backed capability assessment

| Capability | Current verified REST contract | Status |
|---|---|---|
| Equity/spot gainers and losers | `GET /api/market-movers/`, provider fields normalized by Market Movers Engine | Implemented |
| Market indices | `GET /api/market-overview/` returns indices with last price only | Available as index snapshots; no verified previous close/change series for index performance chart |
| Historical OHLCV | `GET /api/market-charts/` returns timestamp, OHLC and optional volume | Implemented |
| Technical indicators | Derived deterministically from loaded OHLCV; VWAP requires volume | Implemented |
| Sector constituents and sector performance | No verified sector constituents / sector historical series endpoint in audited route set | Blocked on data contract |
| Full market breadth universe | Movers endpoint returns a bounded provider top-movers list, not full listed-universe advances/declines | Partial only; do not label top-movers sample as full-market breadth |
| Futures price + open interest | No verified futures quote/history response contract exposing both comparable price and OI observations in audited route set | Blocked on derivatives contract |
| Option-chain CE/PE OI, OI change, expiry, PCR | No verified option-chain route or response schema in audited route set | Blocked on derivatives contract |
| Historical OI time series | No verified provider endpoint/contract | Blocked |
| Continuous WebSocket ticks | No verified subscription contract in audited route set | Not claimed; quote REST polling remains distinct |

## Integrity constraints

- No simulated or hardcoded market values.
- No equity volume used as a proxy for futures OI.
- No spot values substituted for futures contracts.
- No option-chain PCR, writer positioning, OI build-up or support/resistance inferred without actual option-chain observations.
- REST quote retrieval time is not represented as exchange tick time.
- MrChartist source/assets are not copied. The reference project's PolyForm Noncommercial licence is a separate commercial-use gate.

## Verification

GitHub Actions is the verification authority for this branch. The current CI run must complete after the indicator additions. No production/runtime smoke test is claimed. AWS, gateway, secrets, deployment and the existing Markets workflow are outside this change.
