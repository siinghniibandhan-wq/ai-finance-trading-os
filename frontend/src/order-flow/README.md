# Order Flow workspace

The Financial OS navigation exposes **Order Flow** as a separate workspace alongside the existing **Markets** page. The existing Markets workspace and its APIs remain separate.

## Phase 1 — interactive preview

The workspace includes the Nifty 50 / All F&O universe selector, bullish and bearish ranked lists, futures-flow overview chart, sector rail with sector filtering, selected-instrument detail, support/resistance, conviction checks, and an illustrative option open-interest profile. Universe and selected instrument preferences persist in the browser when storage is available. Keyboard Escape closes a pinned detail; arrow keys move through its ranked side list. The chart and ranked lists share instrument selection.

**Data limitation:** every futures, OI, option, sector and conviction value is deterministic simulated demo data. No live market feed, freshness timestamp, reconnect or retry is claimed or displayed. Do not use this preview as live market information or trading advice.

## Phase 2 — explicitly deferred

Live futures prices and open interest, contract-month aggregation, full option-chain data, strike-wise CE/PE open interest, historical OI comparisons, streaming updates, feed freshness/retry, and m.Stock gateway configuration remain Phase 2. They require a separately reviewed implementation and explicit approval before any production, AWS, credential, or broker changes.

## Source parity status

This workspace is an adapted preview, not a complete port of the source project's full-width continuous Flow Diagram and all its chart-focus, crosshair, popup, and feed lifecycle behavior. Those items must not be represented as complete until separately implemented and verified. The existing implementation is retained rather than replacing the application with source files that depend on the source project's unrelated application framework.

## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Use is subject to those terms. Any commercial use requires a separate licence from the rights holder.
