# Advanced Chart Phase 2 — implementation status

Branch: `feature/market-flow-chart-suite-stage-1`  
PR: #219 (draft; not merged)

## Implemented

- Gainer and Loser Scanner views use authenticated `GET /api/market-movers/` with provider-row validation, symbol/company search, NSE/BSE filter, ranked percentage bars, reported-volume summary and bounded 30-second refresh while visible.
- Scanner row selection opens the existing Advanced Chart with the selected instrument.
- Price chart modes: Candlestick, OHLC Bar, Line, Area and Heikin-Ashi (derived from validated provider OHLC).
- Technical overlays: SMA 20, EMA 20, Bollinger Bands (20, 2) and intraday VWAP. VWAP resets by India trading-session date and requires positive volume on every candle.
- Indicator pane: RSI 14 and MACD (12, 26, 9), derived from loaded provider closes.
- Historical OHLCV uses authenticated `GET /api/market-charts/`; the LTP marker uses authenticated REST quote snapshots. Quote snapshots are not represented as WebSocket ticks.
- Existing Markets tab and existing Market Flow board/workflow are preserved.

## Provider contracts — verified documentation vs application wiring

### m.Stock REST and WebSocket

- The current gateway source reviewed on 18 November exposes authentication, LTP/quote, historical candles, script master, gainers/losers and index quote. It does not contain option-chain proxy routes or a persistent market-data WebSocket worker.
- m.Stock Type A option-chain documentation labels the option-chain APIs “Coming Soon”; this is not a dependable Type A integration contract.
- m.Stock Type B documents option-chain master and option-chain data endpoints. The master endpoint itself is marked “coming soon”. The option-chain data endpoint uses Type B Bearer JWT plus X-PrivateKey authentication, unlike the Type A token authentication currently implemented by the gateway. It is documented but not wired into this application.
- m.Stock Type A and Type B both document subscription-based WebSocket market data. The Type A packet schema includes OI, OI high/low and exchange timestamps; Type B full quote packets include OI and OI percentage plus exchange timestamps. The current gateway source does not implement the WebSocket connection, subscription lifecycle, binary decoder or a REST snapshot/cache contract for those fields.
- The m.Stock docs describe market-data APIs and schemas; they do not provide an app-ready sector constituent universe or a full listed-market advance/decline universe.

### Capability status

| Capability | Current evidence | Status |
|---|---|---|
| Equity/spot gainers and losers | Existing Type A gateway route and backend `GET /api/market-movers/` | Implemented |
| Market index snapshots | Existing gateway `/index-quote` and backend index/overview routes | Snapshot only |
| Historical OHLCV | Existing gateway historical route and backend `GET /api/market-charts/` | Implemented |
| Technical indicators | Deterministic derivations from loaded OHLCV | Implemented |
| Sector index performance | Index quote capability exists, but no verified sector-index symbol universe / historical index-token contract has been validated end-to-end | Not implemented |
| Sector constituents / sector breadth | No verified constituent mapping or full-universe advances/declines feed | Blocked on source contract |
| Full-market breadth | Bounded top-movers endpoint is not a full market universe | Blocked on universe data |
| Futures price + OI history | Documented WebSocket packet fields can expose live OI, but no active gateway stream/decoder/cache contract exists in current source | Blocked on gateway stream integration |
| Option-chain CE/PE OI, OI change, expiry and PCR | Type B endpoint documented, but Type B auth/master are not wired; Type A chain docs marked coming soon | Blocked on supported auth + master contract |
| Historical OI time series | No verified historical OI endpoint in the current Type A integration | Blocked; WebSocket capture would only build a forward time series from first successful subscription |
| Continuous WebSocket ticks | Provider protocol documented, but current gateway source has no worker or subscription/snapshot routes | Not connected |

## Integrity and preservation constraints

- No simulated or hardcoded market values.
- No equity volume used as a proxy for futures OI.
- No spot values substituted for futures contracts.
- No option-chain PCR, writer positioning or OI-derived support/resistance without actual option-chain observations.
- Exchange timestamps must remain distinct from backend retrieval timestamps.
- No AWS deployment, secrets, credentials, or runtime configuration changes in this PR.
- MrChartist source/assets are not copied; its licence remains a separate commercial-use gate.

## Verification

- Latest CI run on commit `b59f76f`: frontend production build, frontend regression checks, backend regression tests and repository secret scan all passed.
- No production/runtime smoke test is claimed.
- Provider-dependent items above require additional gateway source integration and a verified provider instrument/expiry master before they can be called complete.
