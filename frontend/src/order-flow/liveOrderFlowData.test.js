import test from "node:test";
import assert from "node:assert/strict";
import {
  buildLiveOrderFlow,
  formatMarketNumber,
  formatMarketTimestamp,
} from "./liveOrderFlowData.js";

test("never creates live rows from a disconnected or simulated-only snapshot", () => {
  const result = buildLiveOrderFlow({
    status: "success",
    feed: { status: "disconnected" },
    futures_contracts: [{ symbol: "NIFTY", price: 25000 }],
  });

  assert.equal(result.isLive, false);
  assert.deepEqual(result.futures, []);
  assert.deepEqual(result.options, []);
  assert.deepEqual(result.optionOiByStrike, []);
});

test("maps only provider futures, options and option OI without inventing change or candles", () => {
  const result = buildLiveOrderFlow({
    status: "success",
    as_of: "2026-11-18T09:30:00+00:00",
    feed: { status: "fresh", age_seconds: 1 },
    stream: { running: true, connected: true },
    futures_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", exchange: "NFO",
        expiry: "2026-11-26", price: 25010.5, volume: 1000, oi: 50000 },
      { symbol: "BANKNIFTY", price: null },
    ],
    option_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOV25000CE", expiry: "2026-11-26",
        strike: 25000, option_type: "CE", oi: 12000 },
    ],
    option_oi_by_strike: [
      { strike: 25000, ce_oi: 12000, pe_oi: 14000 },
    ],
  });

  assert.equal(result.isLive, true);
  assert.deepEqual(result.underlyings, ["NIFTY"]);
  assert.equal(result.futures[0].price, 25010.5);
  assert.equal(result.futures[0].volume, 1000);
  assert.equal(result.futures[0].oi, 50000);
  assert.equal(result.options[0].optionType, "CE");
  assert.deepEqual(result.optionOiByStrike, [
    { strike: 25000, callOi: 12000, putOi: 14000 },
  ]);
  assert.equal("changePct" in result.futures[0], false);
  assert.equal("candles" in result.futures[0], false);
});

test("filters the stream to the selected underlying", () => {
  const snapshot = {
    status: "success",
    feed: { status: "fresh" },
    futures_contracts: [
      { symbol: "NIFTY", price: 25000 },
      { symbol: "BANKNIFTY", price: 56000 },
    ],
    option_contracts: [],
    option_oi_by_strike: [],
  };

  assert.deepEqual(buildLiveOrderFlow(snapshot, "NIFTY").underlyings, ["NIFTY"]);
});

test("formats missing market values and timestamps without fabricated defaults", () => {
  assert.equal(formatMarketNumber(null), "—");
  assert.equal(formatMarketNumber(25000.5), "25,000.5");
  assert.equal(formatMarketTimestamp(null), "—");
});
