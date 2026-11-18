import test from "node:test";
import assert from "node:assert/strict";
import { mapLiveOrderFlowSnapshot } from "./liveOrderFlowData.js";

const snapshot = {
  status: "success",
  as_of: "2026-11-18T04:00:00Z",
  feed: { status: "fresh", age_seconds: 2 },
  futures_contracts: [
    { symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", exchange: "NFO", expiry: "2026-11-26", price: 25012.5, previous_close: 25000, volume: 1200, oi: 450000, instrument_token: 101 },
    { symbol: "BANKNIFTY", tradingsymbol: "BANKNIFTY26NOVFUT", exchange: "NFO", expiry: "2026-11-26", price: 55000, previous_close: 54800, volume: 900, oi: 210000, instrument_token: 102 },
  ],
  option_contracts: [
    { symbol: "NIFTY", exchange: "NFO", strike: 25000, option_type: "CE", oi: 12000 },
    { symbol: "NIFTY", exchange: "NFO", strike: 25000, option_type: "PE", oi: 14000 },
  ],
  option_oi_by_strike: [],
};

test("builds the Market Flow universe exclusively from fresh provider contracts", () => {
  const result = mapLiveOrderFlowSnapshot(snapshot);
  assert.equal(result.isLive, true);
  assert.equal(result.stocks.length, 2);
  assert.equal(result.stocks[0].symbol, "NIFTY");
  assert.equal(result.stocks[0].price, 25012.5);
  assert.equal(result.stocks[0].changePct, 0.05);
  assert.equal(result.stocks[0].volume, 1200);
  assert.equal(result.stocks[0].oi, 450000);
  assert.deepEqual(result.stocks[0].strikes, [{ strike: 25000, put: 14000, call: 12000 }]);
  assert.equal(result.stocks[0].simulated, undefined);
});

test("does not create a demo universe when feed is missing, stale, or disconnected", () => {
  for (const feed of [undefined, { status: "stale" }, { status: "disconnected" }]) {
    const result = mapLiveOrderFlowSnapshot({ ...snapshot, feed });
    assert.equal(result.isLive, false);
    assert.deepEqual(result.stocks, []);
  }
});

test("does not treat non-NFO, malformed or price-less contracts as live instruments", () => {
  const result = mapLiveOrderFlowSnapshot({
    ...snapshot,
    futures_contracts: [
      { symbol: "BAD", exchange: "NSE", price: 10 },
      { symbol: "BROKEN", exchange: "NFO", price: "NaN" },
      { symbol: "EMPTY", exchange: "NFO", price: null },
    ],
  });
  assert.equal(result.isLive, false);
  assert.deepEqual(result.stocks, []);
});
