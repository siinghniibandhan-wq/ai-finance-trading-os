import test from"node:test";import assert from"node:assert/strict";import{normalizeOrderFlow,summarizeOrderFlow,sortOrderFlow,buildChartFlowPoints,buildMarketFlowBoard,buildDistributionDots,normalizeSectorMovers,filterOrderFlow,buildHistoricalFlowSeries,summarizeSectorMoverSample}from"./orderFlowModel.js";
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
