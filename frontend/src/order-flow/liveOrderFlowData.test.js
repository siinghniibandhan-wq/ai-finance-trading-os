import test from "node:test";
import assert from "node:assert/strict";
import {
  buildLiveOrderFlow,
  formatMarketNumber,
  formatMarketPercent,
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

test("maps provider change and OHLC without inventing historical candles", () => {
  const result = buildLiveOrderFlow({
    status: "success",
    as_of: "2026-11-18T09:30:00+00:00",
    feed: { status: "fresh", age_seconds: 1 },
    stream: { running: true, connected: true },
    futures_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", exchange: "NFO",
        expiry: "2026-11-26", price: 25010.5, volume: 1000, oi: 50000,
        change_pct: -0.2, ohlc: { open: 25020, high: 25100, low: 24900, close: 25000 },
        last_traded_quantity: 25, total_buy_quantity: 600, total_sell_quantity: 400 },
      { symbol: "BANKNIFTY", price: null },
    ],
    option_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOV25000CE", expiry: "2026-11-26",
        strike: 25000, option_type: "CE", oi: 12000 },
    ],
    option_oi_by_strike: [
      { symbol: "NIFTY", expiry: "2026-11-26", strike: 25000, ce_oi: 12000, pe_oi: 14000 },
    ],
  });

  assert.equal(result.isLive, true);
  assert.deepEqual(result.underlyings, ["NIFTY"]);
  assert.equal(result.futures[0].price, 25010.5);
  assert.equal(result.futures[0].volume, 1000);
  assert.equal(result.futures[0].oi, 50000);
  assert.equal(result.futures[0].changePct, -0.2);
  assert.equal(result.futures[0].buySellBalancePct, 20);
  assert.equal(result.futures[0].lastTradedQuantity, 25);
  assert.deepEqual(result.futures[0].ohlc, { open: 25020, high: 25100, low: 24900, close: 25000 });
  assert.equal(result.options[0].optionType, "CE");
  assert.deepEqual(result.optionOiByStrike, [
    { symbol: "NIFTY", expiry: "2026-11-26", strike: 25000, callOi: 12000, putOi: 14000 },
  ]);
  assert.equal("changePct" in result.futures[0], true);
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
  assert.equal(formatMarketPercent(-0.2), "-0.20%");
  assert.equal(formatMarketPercent(0.5), "+0.50%");
  assert.equal(formatMarketTimestamp(null), "—");
});


test("appends only fresh provider futures ticks to live chart history", async () => {
  const { appendLivePriceHistory } = await import("./liveOrderFlowData.js");
  const history = appendLivePriceHistory([], {
    status: "success",
    as_of: "2026-11-19T03:45:00Z",
    feed: { status: "fresh" },
    futures_contracts: [
      { symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", price: 25010, exchange_timestamp: "2026-11-19T03:44:59Z" },
      { symbol: "BANKNIFTY", tradingsymbol: "BANKNIFTY26NOVFUT", price: null, exchange_timestamp: "2026-11-19T03:44:59Z" },
    ],
  });
  assert.deepEqual(history, [{
    symbol: "NIFTY",
    contract: "NIFTY26NOVFUT",
    price: 25010,
    timestamp: "2026-11-19T03:44:59Z",
  }]);
});

test("does not append stale or disconnected provider values to chart history", async () => {
  const { appendLivePriceHistory } = await import("./liveOrderFlowData.js");
  const existing = [{ symbol: "NIFTY", contract: "NIFTY26NOVFUT", price: 25000, timestamp: "2026-11-19T03:40:00Z" }];
  assert.equal(appendLivePriceHistory(existing, {
    status: "success", feed: { status: "stale" },
    futures_contracts: [{ symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", price: 26000, received_at: "2026-11-19T03:45:00Z" }],
  }), existing);
});

test("replaces duplicate contract timestamps and enforces the chart history cap", async () => {
  const { appendLivePriceHistory } = await import("./liveOrderFlowData.js");
  const first = { symbol: "NIFTY", contract: "NIFTY26NOVFUT", price: 25000, timestamp: "2026-11-19T03:40:00Z" };
  const replaced = appendLivePriceHistory([first], {
    status: "success", feed: { status: "fresh" },
    futures_contracts: [{ symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", price: 25001, exchange_timestamp: first.timestamp }],
  });
  assert.equal(replaced.length, 1);
  assert.equal(replaced[0].price, 25001);
  const capped = appendLivePriceHistory([], {
    status: "success", feed: { status: "fresh" },
    futures_contracts: Array.from({ length: 5 }, (_, index) => ({
      symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", price: 25000 + index,
      received_at: `2026-11-19T03:4${index}:00Z`,
    })),
  }, 3);
  assert.equal(capped.length, 3);
});
