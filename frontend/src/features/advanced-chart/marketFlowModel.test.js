import test from "node:test";
import assert from "node:assert/strict";
import { normalizeMarketFlow } from "./marketFlowModel.js";

test("normalizes provider gainers and losers into directional groups", () => {
  const result = normalizeMarketFlow({
    market_movers: {
      gainers: [
        { symbol: "AAA", exchange: "NSE", ltp: "125.5", percent_change: "2.4", name: "Alpha Ltd" },
        { symbol: "FLAT", exchange: "NSE", ltp: 100, percent_change: 0 },
      ],
      losers: [
        { symbol: "BBB", exchange: "BSE", ltp: 80, percent_change: -1.7 },
      ],
    },
  });

  assert.deepEqual(result.bullish.map((item) => item.symbol), ["AAA"]);
  assert.deepEqual(result.bearish.map((item) => item.symbol), ["BBB"]);
  assert.deepEqual(result.unchanged.map((item) => item.symbol), ["FLAT"]);
  assert.equal(result.bullish[0].lastPrice, 125.5);
  assert.equal(result.bullish[0].changePercent, 2.4);
});

test("omits malformed rows instead of inventing price or direction", () => {
  const result = normalizeMarketFlow({
    market_movers: {
      gainers: [
        { symbol: "NO-LTP", exchange: "NSE", percent_change: 2 },
        { symbol: "NO-CHANGE", exchange: "NSE", ltp: 100 },
        { symbol: "", exchange: "NSE", ltp: 100, percent_change: 1 },
      ],
      losers: "invalid",
    },
  });

  assert.deepEqual(result.bullish, []);
  assert.deepEqual(result.bearish, []);
  assert.deepEqual(result.unchanged, []);
});

test("does not infer exchange when provider does not supply a supported exchange", () => {
  const result = normalizeMarketFlow({
    market_movers: {
      gainers: [{ symbol: "AAA", ltp: 100, percent_change: 1 }],
      losers: [],
    },
  });

  assert.deepEqual(result.bullish, []);
});


test("builds connected flow paths from each provider-reported mover and its actual percentage change", async () => {
  const { buildMarketFlowDiagram } = await import("./marketFlowModel.js");
  const groups = normalizeMarketFlow({ market_movers: {
    gainers: [
      { symbol: "AAA", exchange: "NSE", ltp: 125, percent_change: 4.2 },
      { symbol: "BBB", exchange: "NSE", ltp: 80, percent_change: 1.1 },
    ],
    losers: [{ symbol: "CCC", exchange: "BSE", ltp: 55, percent_change: -3.4 }],
  }});
  const diagram = buildMarketFlowDiagram(groups, { width: 1200, height: 700 });
  assert.equal(diagram.connections.length, 3);
  assert.deepEqual(diagram.connections.map((item) => item.symbol), ["AAA", "BBB", "CCC"]);
  assert.ok(diagram.connections[0].endY < diagram.zeroY);
  assert.ok(diagram.connections[2].endY > diagram.zeroY);
  assert.match(diagram.connections[0].path, /^M .* C .*$/);
  assert.ok(diagram.connections.every((item) => item.path.includes(String(item.endY))));
});

test("does not draw flow paths for invalid or unchanged provider rows", async () => {
  const { buildMarketFlowDiagram } = await import("./marketFlowModel.js");
  const groups = normalizeMarketFlow({ market_movers: {
    gainers: [{ symbol: "BAD", exchange: "NSE", ltp: null, percent_change: 2 }],
    losers: [{ symbol: "FLAT", exchange: "NSE", ltp: 100, percent_change: 0 }],
  }});
  assert.deepEqual(buildMarketFlowDiagram(groups, { width: 900, height: 500 }).connections, []);
});
