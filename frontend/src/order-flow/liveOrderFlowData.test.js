import test from "node:test";
import assert from "node:assert/strict";
import { mapLiveOrderFlowSnapshot } from "./liveOrderFlowData.js";

const stocks = [{ symbol: "NIFTY", future: 25000, oi: 10, candles: [{ change: 1 }], strikes: [{ strike: 25000, put: 1, call: 2 }] }, { symbol: "BANKNIFTY" }];

test("overlays fresh exact NFO futures and option OI without replacing simulated analytics", () => {
  const result = mapLiveOrderFlowSnapshot({
    status: "success", as_of: "2026-11-18T04:00:00Z", feed: { status: "fresh", age_seconds: 2 },
    futures_contracts: [{ symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", exchange: "NFO", expiry: "2026-11-26", price: 25012.5, volume: 1200, oi: 450000, instrument_token: 101 }],
    option_contracts: [
      { symbol: "NIFTY", exchange: "NFO", strike: 25000, option_type: "CE", oi: 12000 },
      { symbol: "NIFTY", exchange: "NFO", strike: 25000, option_type: "PE", oi: 14000 },
    ],
    option_oi_by_strike: [],
  }, stocks);
  const live = result.stocks[0].liveMarket;
  assert.equal(result.isLive, true);
  assert.equal(live.price, 25012.5);
  assert.equal(live.volume, 1200);
  assert.equal(live.oi, 450000);
  assert.deepEqual(live.strikes, [{ strike: 25000, put: 14000, call: 12000 }]);
  assert.equal(result.stocks[0].future, 25000);
  assert.deepEqual(result.stocks[0].candles, [{ change: 1 }]);
  assert.equal(result.stocks[1].liveMarket, undefined);
});

test("does not overlay disconnected, stale, or non-NFO data", () => {
  const stale = mapLiveOrderFlowSnapshot({ status: "success", feed: { status: "stale" }, futures_contracts: [{ symbol: "NIFTY", exchange: "NFO", price: 10 }] }, stocks);
  assert.equal(stale.isLive, false);
  assert.equal(stale.stocks[0].liveMarket, undefined);
  const wrongExchange = mapLiveOrderFlowSnapshot({ status: "success", feed: { status: "fresh" }, futures_contracts: [{ symbol: "NIFTY", exchange: "NSE", price: 10 }] }, stocks);
  assert.equal(wrongExchange.isLive, false);
  assert.equal(wrongExchange.stocks[0].liveMarket, undefined);
});

test("ignores malformed provider collections and non-finite prices", () => {
  const result = mapLiveOrderFlowSnapshot({ status: "success", feed: { status: "fresh" }, futures_contracts: [{ symbol: "NIFTY", exchange: "NFO", price: "NaN" }] }, stocks);
  assert.equal(result.isLive, false);
  assert.equal(result.stocks[0].liveMarket, undefined);
});
