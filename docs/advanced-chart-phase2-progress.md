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

## REST provider contracts — verified documentation vs application wiring

- The current Type A gateway exposes authentication, LTP/quote, historical candles, script master, gainers/losers and index quote through REST.
- m.Stock Type A option-chain documentation labels the option-chain APIs “Coming Soon”; this is not a dependable REST integration contract.
- m.Stock Type B documents option-chain master and option-chain data REST endpoints. The master endpoint is marked “coming soon”. The data endpoint requires Type B Bearer JWT plus X-PrivateKey authentication, unlike the Type A authentication currently implemented by the gateway. It is documented but not wired into this application.
- No verified REST endpoint is currently available in the integrated Type A contract for futures OI history, option-chain OI/PCR, or historical OI time series.
- The m.Stock REST docs do not provide an app-ready sector constituent universe or a full listed-market advance/decline universe.

## Capability status

| Capability | Current evidence | Status |
|---|---|---|
| Equity/spot gainers and losers | Existing Type A gateway route and backend `GET /api/market-movers/` | Implemented |
| Market index snapshots | Existing gateway `/index-quote` and backend index/overview routes | Snapshot only |
| Historical OHLCV | Existing gateway historical route and backend `GET /api/market-charts/` | Implemented |
| Latest quote / LTP marker | Authenticated REST quote snapshot | Implemented |
| Technical indicators | Deterministic derivations from loaded OHLCV | Implemented |
| Sector index performance | Index quote capability exists, but no verified sector-index symbol universe / historical index-token contract has been validated end-to-end | Not implemented |
| Sector constituents / sector breadth | No verified constituent mapping or full-universe advances/declines REST feed | Not available |
| Full-market breadth | Bounded top-movers endpoint is not a full market universe | Not available |
| Futures price + OI history | No verified REST endpoint in the current Type A integration | Not available |
| Option-chain CE/PE OI, OI change, expiry and PCR | Type B REST endpoint documented, but Type B auth/master are not wired; Type A chain docs marked coming soon | Not integrated |
| Historical OI time series | No verified historical OI REST endpoint in the current Type A integration | Not available |
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
