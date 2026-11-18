import test from "node:test";
import assert from "node:assert/strict";
import { mergeMarketOverview } from "./marketOverviewState.js";

test("retains only the failed index and mover section from the last successful response", () => {
  const previous = {
    indices: [
      { name: "NIFTY 50", last_price: 22000 },
      { name: "SENSEX", last_price: 72000 },
    ],
    market_movers: {
      gainers: [{ symbol: "OLD_GAINER" }],
      losers: [{ symbol: "OLD_LOSER" }],
    },
  };
  const next = {
    status: "partial",
    indices: [{ name: "NIFTY 50", last_price: 22100 }],
    market_movers: {
      gainers: [],
      losers: [{ symbol: "NEW_LOSER" }],
    },
    errors: [
      { source: "market_indices", name: "SENSEX", message: "timeout" },
      { source: "market_movers", type: "gainers", message: "provider error" },
    ],
  };

  const merged = mergeMarketOverview(previous, next);

  assert.deepEqual(merged.indices, [
    { name: "NIFTY 50", last_price: 22100 },
    { name: "SENSEX", last_price: 72000 },
  ]);
  assert.deepEqual(merged.market_movers.gainers, [{ symbol: "OLD_GAINER" }]);
  assert.deepEqual(merged.market_movers.losers, [{ symbol: "NEW_LOSER" }]);
  assert.deepEqual(merged.stale_sections, { indices: ["SENSEX"], gainers: true, losers: false });
});

test("replaces prior data after a complete successful refresh", () => {
  const previous = {
    indices: [{ name: "NIFTY 50", last_price: 22000 }],
    market_movers: { gainers: [{ symbol: "OLD" }], losers: [] },
  };
  const next = {
    status: "success",
    indices: [{ name: "NIFTY 50", last_price: 22100 }],
    market_movers: { gainers: [{ symbol: "NEW" }], losers: [] },
    errors: [],
  };

  const merged = mergeMarketOverview(previous, next);

  assert.deepEqual(merged.indices, next.indices);
  assert.deepEqual(merged.market_movers, next.market_movers);
  assert.deepEqual(merged.stale_sections, { indices: [], gainers: false, losers: false });
});
