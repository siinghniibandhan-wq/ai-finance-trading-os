import test from "node:test";
import assert from "node:assert/strict";
import { mapLiveOrderFlowSnapshot } from "./liveOrderFlowData.js";

test("maps provider futures and option OI into display rows without demo-derived metrics", () => {
  const result = mapLiveOrderFlowSnapshot({
    status: "success",
    source: "m.Stock via Financial OS market-stream gateway",
    as_of: "2026-11-18T04:00:00Z",
    feed: { status: "fresh", age_seconds: 2 },
    futures_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", expiry: "2026-11-26", price: 25012.5, volume: 1200, oi: 450000, exchange: "NFO" },
    ],
    option_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOV25000CE", expiry: "2026-11-26", strike: 25000, option_type: "CE", price: 125.5, volume: 100, oi: 12000 },
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOV25000PE", expiry: "2026-11-26", strike: 25000, option_type: "PE", price: 130, volume: 150, oi: 14000 },
    ],
    option_oi_by_strike: [{ strike: 25000, ce_oi: 12000, pe_oi: 14000 }],
  });

  assert.equal(result.feedStatus, "fresh");
  assert.equal(result.futures.length, 1);
  assert.deepEqual(result.futures[0], {
    symbol: "NIFTY", contract: "NIFTY26NOVFUT", expiry: "2026-11-26",
    price: 25012.5, volume: 1200, oi: 450000, exchange: "NFO",
  });
  assert.deepEqual(result.optionOi, [{ strike: 25000, ceOi: 12000, peOi: 14000 }]);
  assert.equal("changePct" in result.futures[0], false);
  assert.equal("candles" in result.futures[0], false);
  assert.equal("pcr" in result.optionOi[0], false);
});

test("does not turn empty or disconnected snapshots into live data", () => {
  const result = mapLiveOrderFlowSnapshot({
    status: "success",
    feed: { status: "disconnected", age_seconds: null },
    futures_contracts: [],
    option_contracts: [],
    option_oi_by_strike: [],
  });
  assert.equal(result.feedStatus, "disconnected");
  assert.deepEqual(result.futures, []);
  assert.deepEqual(result.options, []);
  assert.deepEqual(result.optionOi, []);
});

test("rejects malformed provider collections rather than filling them with demo values", () => {
  assert.throws(() => mapLiveOrderFlowSnapshot({
    status: "success", feed: { status: "fresh" },
    futures_contracts: "not-an-array", option_contracts: [], option_oi_by_strike: [],
  }), /invalid futures collection/i);
});
