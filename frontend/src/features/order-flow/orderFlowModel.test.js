import test from"node:test";import assert from"node:assert/strict";import{normalizeOrderFlow,summarizeOrderFlow,sortOrderFlow,buildChartFlowPoints,buildMarketFlowBoard,buildDistributionDots,normalizeSectorMovers,filterOrderFlow,buildHistoricalFlowSeries,summarizeSectorMoverSample,rankSectorIndices,summarizeMoverVolume,buildSectorFlowRows,buildHistoricalCandleGeometry}from"./orderFlowModel.js";
test("normalizes only provider supplied NSE/BSE movers",()=>{const rows=normalizeOrderFlow({market_movers:{gainers:[{symbol:"abc",exchange:"NSE",ltp:"10",percent_change:"2"},{symbol:"bad",exchange:"NFO",ltp:2,percent_change:1}],losers:[{symbol:"xyz",exchange:"BSE",ltp:4,percent_change:-1}]}});assert.deepEqual(rows.map(r=>r.symbol),["ABC","XYZ"]);assert.deepEqual(rows.map(r=>r.direction),["bullish","bearish"]);});
test("summarizes and sorts only normalized provider rows",()=>{const rows=normalizeOrderFlow({market_movers:{gainers:[{symbol:"a",exchange:"NSE",ltp:10,percent_change:1}],losers:[{symbol:"b",exchange:"BSE",ltp:20,percent_change:-2}]}});assert.equal(summarizeOrderFlow(rows).total,2);assert.deepEqual(sortOrderFlow(rows,"changePercent","desc").map(r=>r.symbol),["A","B"]);});
test("builds a zero-centred chart-flow series from provider price changes",()=>{const rows=[{symbol:"UP",changePercent:4,direction:"bullish"},{symbol:"DOWN",changePercent:-2,direction:"bearish"},{symbol:"FLAT",changePercent:0,direction:"unchanged"}];const points=buildChartFlowPoints(rows);assert.equal(points.length,3);assert.equal(points[0].normalizedMove,1);assert.equal(points.find(r=>r.symbol==="DOWN").normalizedMove,-0.5);assert.equal(points.find(r=>r.symbol==="FLAT").normalizedMove,0);});
test("limits chart-flow points and does not invent rows for empty input",()=>{const rows=Array.from({length:5},(_,i)=>({symbol:String(i),changePercent:i,direction:"bullish"}));assert.equal(buildChartFlowPoints(rows,3).length,3);assert.deepEqual(buildChartFlowPoints(null),[]);});


test("builds bullish, bearish and unchanged lanes only from returned instruments", () => {
  const board = buildMarketFlowBoard([
    { symbol: "UP2", changePercent: 2 },
    { symbol: "DOWN2", changePercent: -2 },
    { symbol: "UP1", changePercent: 1 },
    { symbol: "FLAT", changePercent: 0 },
  ], 1);
  assert.deepEqual(board.visibleBullish.map(row => row.symbol), ["UP2"]);
  assert.deepEqual(board.visibleBearish.map(row => row.symbol), ["DOWN2"]);
  assert.deepEqual(board.unchanged.map(row => row.symbol), ["FLAT"]);
  assert.deepEqual(board.counts, { bullish: 2, bearish: 1, unchanged: 1, total: 4 });
});

test("distribution dots retain provider changes and do not invent observations", () => {
  const rows = [{ symbol: "UP", changePercent: 2 }, { symbol: "DOWN", changePercent: -1 }];
  const dots = buildDistributionDots(rows);
  assert.equal(dots.length, 2);
  assert.equal(dots.find(row => row.symbol === "UP").changePercent, 2);
  assert.equal(dots.find(row => row.symbol === "DOWN").changePercent, -1);
  assert.ok(dots.every(dot => Number.isFinite(dot.x) && Number.isFinite(dot.y)));
  assert.deepEqual(buildDistributionDots([]), []);
});


test("normalizes provider-ranked sector movers without inventing sector constituents", () => {
  const rows = normalizeSectorMovers({
    sector: { key: "it", name: "Information Technology" },
    movers: {
      gainers: [{ symbol: "INFY", exchange: "NSE", ltp: 1500, percent_change: 2, volume: 1000 }],
      losers: [{ symbol: "WIPRO", exchange: "NSE", ltp: 400, percent_change: -1, volume: 2000 }],
    },
  });
  assert.deepEqual(rows.map(row => row.symbol), ["INFY", "WIPRO"]);
  assert.ok(rows.every(row => row.sector === "Information Technology"));
  assert.deepEqual(normalizeSectorMovers({ movers: { gainers: [], losers: [] } }), []);
});


test("filters real Chart Flow rows by search, exchange and direction", () => {
  const rows = normalizeOrderFlow({
    market_movers: {
      gainers: [
        { symbol: "INFY", name: "Infosys Limited", exchange: "NSE", ltp: 1500, percent_change: 2 },
        { symbol: "TCS", name: "Tata Consultancy Services", exchange: "NSE", ltp: 4000, percent_change: 1 },
      ],
      losers: [
        { symbol: "WIPRO", name: "Wipro Limited", exchange: "BSE", ltp: 400, percent_change: -1 },
      ],
    },
  });

  assert.deepEqual(
    filterOrderFlow(rows, { query: "infosys", exchange: "NSE", direction: "bullish" }).map(row => row.symbol),
    ["INFY"],
  );
  assert.deepEqual(
    filterOrderFlow(rows, { query: "", exchange: "BSE", direction: "all" }).map(row => row.symbol),
    ["WIPRO"],
  );
});


test("builds historical stock flow only from valid provider OHLCV observations", () => {
  const series = buildHistoricalFlowSeries([
    { timestamp: 1, open: 10, high: 12, low: 9, close: 11, volume: 100 },
    { timestamp: 2, open: 11, high: 13, low: 10, close: 12, volume: 200 },
    { timestamp: 3, open: 12, high: 12, low: 8, close: 9, volume: null },
    { timestamp: 4, open: 0, high: 0, low: 0, close: 0, volume: 500 },
  ]);
  assert.equal(series.length, 3);
  assert.equal(series[0].relativeChange, 0);
  assert.equal(series[1].relativeChange, 100 / 11);
  assert.equal(series[2].relativeChange, -200 / 11);
  assert.equal(series[2].volume, null);
  assert.equal(series[0].open, 10);
  assert.equal(series[0].high, 12);
  assert.equal(series[0].low, 9);
});


test("summarizes sector sample without calling it full-sector performance", () => {
  const summary = summarizeSectorMoverSample([
    { changePercent: 4, direction: "bullish" },
    { changePercent: 2, direction: "bullish" },
    { changePercent: -1, direction: "bearish" },
  ]);
  assert.equal(summary.count, 3);
  assert.equal(summary.medianChangePct, 2);
  assert.equal(summary.bullish, 2);
  assert.equal(summary.bearish, 1);
});


test("sorts symbols in both requested directions and leaves missing metrics last", () => {
  const rows = [
    { symbol: "TCS", volume: 10 },
    { symbol: "INFY", volume: null },
    { symbol: "WIPRO", volume: 5 },
  ];
  assert.deepEqual(sortOrderFlow(rows, "symbol", "asc").map(row => row.symbol), ["INFY", "TCS", "WIPRO"]);
  assert.deepEqual(sortOrderFlow(rows, "symbol", "desc").map(row => row.symbol), ["WIPRO", "TCS", "INFY"]);
  assert.deepEqual(sortOrderFlow(rows, "volume", "desc").map(row => row.symbol), ["TCS", "WIPRO", "INFY"]);
});


test("ranks sectors by provider OHLC percentage change and leaves unavailable changes last", () => {
  const ranked = rankSectorIndices(
    [{ key: "auto", name: "Auto" }, { key: "it", name: "IT" }, { key: "pharma", name: "Pharma" }],
    [
      { key: "auto", percent_change: -1.2 },
      { key: "it", percent_change: 2.5 },
      { key: "pharma", percent_change: null },
    ],
  );
  assert.deepEqual(ranked.map(row => row.key), ["it", "auto", "pharma"]);
});


test("applies selected sort to bullish and bearish market flow lists", () => {
  const rows = [
    { symbol: "A", changePercent: 3, volume: 100 },
    { symbol: "B", changePercent: 2, volume: 500 },
    { symbol: "C", changePercent: -1, volume: 900 },
    { symbol: "D", changePercent: -2, volume: 200 },
  ];
  const board = buildMarketFlowBoard(rows, 12, "volume", "desc");
  assert.deepEqual(board.bullish.map(row => row.symbol), ["B", "A"]);
  assert.deepEqual(board.bearish.map(row => row.symbol), ["C", "D"]);
});


test("keeps strongest bullish and bearish price moves first by default", () => {
  const board = buildMarketFlowBoard([
    { symbol: "UP2", changePercent: 2 },
    { symbol: "UP5", changePercent: 5 },
    { symbol: "DOWN1", changePercent: -1 },
    { symbol: "DOWN4", changePercent: -4 },
  ]);
  assert.deepEqual(board.bullish.map(row => row.symbol), ["UP5", "UP2"]);
  assert.deepEqual(board.bearish.map(row => row.symbol), ["DOWN4", "DOWN1"]);
});


test("summarizes actual volume only for returned movers with volume values", () => {
  const summary = summarizeMoverVolume([
    { direction: "bullish", volume: 100 },
    { direction: "bullish", volume: null },
    { direction: "bearish", volume: 250 },
    { direction: "unchanged", volume: 50 },
  ]);
  assert.deepEqual(summary, {
    bullishVolume: 100,
    bearishVolume: 250,
    unchangedVolume: 50,
    bullishCount: 1,
    bearishCount: 1,
    unchangedCount: 1,
    volumeReported: 3,
  });
});


test("builds a complete sector flow rail while keeping unavailable provider performance null", () => {
  const rows = buildSectorFlowRows(
    [
      { key: "auto", name: "Automobile", index_symbol: "NIFTY AUTO" },
      { key: "it", name: "Information Technology", index_symbol: "NIFTY IT" },
      { key: "pharma", name: "Pharma", index_symbol: "NIFTY PHARMA" },
    ],
    [
      { key: "auto", last_price: 25000, percent_change: -1.2 },
      { key: "it", last_price: 42000, percent_change: 2.5 },
      { key: "pharma", last_price: 18000, percent_change: null },
    ],
  );

  assert.deepEqual(rows.map(row => row.key), ["it", "auto", "pharma"]);
  assert.equal(rows[0].direction, "bullish");
  assert.equal(rows[0].percentChange, 2.5);
  assert.equal(rows[1].direction, "bearish");
  assert.equal(rows[1].lastPrice, 25000);
  assert.equal(rows[2].direction, null);
  assert.equal(rows[2].percentChange, null);
  assert.equal(rows[2].lastPrice, 18000);
});


test("builds candle geometry from actual OHLC values and preserves missing volume", () => {
  const geometry = buildHistoricalCandleGeometry([
    { timestamp: 1, open: 10, high: 13, low: 9, close: 12, volume: 100 },
    { timestamp: 2, open: 12, high: 14, low: 11, close: 11, volume: null },
  ]);
  assert.equal(geometry.length, 2);
  assert.equal(geometry[0].direction, "bullish");
  assert.equal(geometry[1].direction, "bearish");
  assert.equal(geometry[0].volumeHeight, 36);
  assert.equal(geometry[1].volumeHeight, 0);
  assert.ok(geometry.every(item => item.highY <= item.lowY));
  assert.ok(geometry.every(item => item.bodyHeight >= 1));
  assert.equal(buildHistoricalCandleGeometry([]).length, 0);
});


test("keeps dense five-year daily candle bodies within their horizontal slot", () => {
  const rows = Array.from({ length: 1250 }, (_, index) => ({
    timestamp: index + 1,
    open: 100 + index / 100,
    high: 102 + index / 100,
    low: 99 + index / 100,
    close: 101 + index / 100,
    volume: 1000,
  }));
  const geometry = buildHistoricalCandleGeometry(rows);
  const slotWidth = (720 - 48) / rows.length;
  assert.equal(geometry.length, rows.length);
  assert.ok(geometry.every(candle => candle.bodyWidth <= slotWidth));
});

test("rejects impossible OHLC ranges from candle geometry", () => {
  const geometry = buildHistoricalCandleGeometry([
    { timestamp: 1, open: 10, high: 9, low: 8, close: 10, volume: 10 },
    { timestamp: 2, open: 10, high: 12, low: 11, close: 9, volume: 10 },
    { timestamp: 3, open: 10, high: 12, low: 8, close: 11, volume: 10 },
  ]);
  assert.equal(geometry.length, 1);
  assert.equal(geometry[0].timestamp, 3);
});
