# Order Flow workspace

The Financial OS navigation exposes **Order Flow** as a separate workspace alongside the existing **Markets** page. The existing Markets workspace and its APIs remain separate.

## Phase 1 — interactive source-inspired board

The workspace now has a continuous left-to-right desktop Flow Diagram (futures fan → flow gate → bullish/bearish ranked instruments → featured position cards), with split desktop, stacked tablet and tabbed mobile layouts based on available workspace width. It includes linked chart/list focus, selectable futures curves, crosshair, sector highlighting, pinned instrument details, option-OI profile, support/resistance, conviction checks, previous/next navigation, Escape-to-close, keyboard focus trapping and restoration, and persistent universe/instrument preferences.

The diagram is an adaptation of the source project's interaction and layout model to Financial OS's existing React application and demo data model; it is not a verbatim component transplant from the source application's separate data architecture.

**Data limitation:** every futures, OI, option, sector and conviction value remains deterministic simulated demo data. No live market feed, freshness timestamp, reconnect or retry is claimed or displayed. Do not use this preview as live market information or trading advice.

## Phase 2 — explicitly deferred

Live futures prices and open interest, contract-month aggregation, full option-chain data, strike-wise CE/PE open interest, historical OI comparisons, streaming updates, feed freshness/retry, and m.Stock gateway configuration remain Phase 2. They require a separately reviewed implementation and explicit approval before any production, AWS, credential, or broker changes.

## Attribution and licence

The source Order Flow project is by Mr. Chartist (https://mrchartist.com), from https://github.com/MrChartist/order-flow. Its original PolyForm Noncommercial License 1.0.0 and required copyright notice are preserved in this directory's `LICENSE` file. Use is subject to those terms. Any commercial use requires a separate licence from the rights holder.
