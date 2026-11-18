# Advanced Chart Phase 2 — implementation status

Branch: `feature/market-flow-chart-suite-stage-1`  
PR: #219 (draft; not merged)

## Implemented in this branch

- Isolated REST-backed Gainer and Loser Scanner views using authenticated `GET /api/market-movers/`.
- Provider-row validation for symbol, NSE/BSE exchange, positive LTP and percentage change; scanner direction is checked against the provider's percentage change.
- Search/filter/ranked percentage-move chart, reported-volume summary and bounded 30-second refresh while the view is visible.
- Scanner instrument selection opens the existing Advanced Chart.
- Price chart modes: Candlestick, OHLC Bar, Line, Area and Heikin-Ashi (derived from provider OHLC).
- Technical overlays: SMA 20, EMA 20, Bollinger Bands (20, 2) and intraday VWAP. VWAP resets on each India trading-session date and is available only when every loaded candle has valid positive volume.
- Separate indicator pane: RSI 14 and MACD (12, 26, 9), calculated from loaded provider closes.
- Historical chart candles use authenticated REST `GET /api/market-charts/`; the latest-price line uses authenticated REST `GET /api/market-quote/` snapshots. Quote polling is not described as a WebSocket tick feed.
- Existing Market Flow board and Markets tab remain outside the changes.

## Provider-backed capability assessment

| Capability | Verified REST contract | Status |
|---|---|---|
| Equity/spot gainers and losers | `GET /api/market-movers/` returns provider-normalized top movers, with a maximum limit of 100 | Implemented |
| Market indices | `GET /api/market-overview/` returns index last-price snapshots | Snapshot only; no verified previous-close or historical index series for a performance chart |
| Historical OHLCV | `GET /api/market-charts/` returns timestamp, OHLC and optional volume | Implemented |
| Technical indicators | Derived deterministically from loaded OHLCV; VWAP requires positive volume and resets per India session date | Implemented |
| Sector constituents and sector performance | No verified sector constituents or sector historical-series endpoint in the audited route set | Blocked on data contract |
| Full-market breadth | Movers endpoint returns a bounded top-movers sample, not the full listed-universe advances/declines | Not implemented; must not be labelled full-market breadth |
| Futures price plus open interest | No verified futures response contract exposing comparable price and OI observations | Blocked on derivatives contract |
| Option-chain CE/PE OI, OI change, expiry and PCR | No verified option-chain route or response schema | Blocked |
| Historical OI time series | No verified provider endpoint/contract | Blocked |
| Continuous WebSocket ticks | No verified subscription contract in the audited route set | Not claimed; quote REST polling remains distinct |

## Integrity and preservation constraints

- No simulated or hardcoded market values.
- No equity volume used as a proxy for futures OI.
- No spot values substituted for futures contracts.
- No option-chain PCR, writer positioning, OI build-up or OI-derived support/resistance without actual option-chain observations.
- REST quote retrieval time is not represented as exchange tick time.
- MrChartist source/assets are not copied. Its licence remains a separate commercial-use gate.
- No AWS, gateway, credentials, deployment or existing Markets workflow changes.

## Verification

- GitHub Actions on the previous feature commit passed frontend production build, frontend regression checks, backend regression tests and repository secret scan.
- The latest VWAP session-reset change includes a regression test; its new commit still requires a fresh CI run before this incremental fix can be called verified.
- No production/runtime smoke test is claimed.
