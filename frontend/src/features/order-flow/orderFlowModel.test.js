import test from"node:test";import assert from"node:assert/strict";import{normalizeOrderFlow,summarizeOrderFlow,sortOrderFlow,buildChartFlowPoints,buildMarketFlowBoard,buildDistributionDots}from"./orderFlowModel.js";
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


test("normalizes historical OHLCV candles into chart-safe time and price values", async () => {
  const { normalizeMarketFlowCandles } = await import("./orderFlowModel.js");
  const candles = normalizeMarketFlowCandles([
    [1795080600, "100", "105", "98", "103", "1200"],
    ["invalid", 100, 105, 98, 103, 1200],
    [1795080660, 100, 99, 98, 101, 1200],
    [1795080720, 100, 105, 98, 103, -1],
  ]);
  assert.deepEqual(candles, [
    { time: 1795080600, open: 100, high: 105, low: 98, close: 103, volume: 1200 },
  ]);
});
