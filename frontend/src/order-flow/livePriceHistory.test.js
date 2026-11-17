import test from "node:test";
import assert from "node:assert/strict";

import { appendLivePricePoint } from "./livePriceHistory.js";

test("records one real futures-price point per new exchange timestamp", () => {
  const first = appendLivePricePoint([], {
    feed: { status: "fresh", last_tick_at: "2026-11-18T03:00:00+00:00" },
    futures_contracts: [
      { tradingsymbol: "NIFTY26NOVFUT", price: 25000 },
      { tradingsymbol: "NIFTY27JANFUT", price: 25100 },
    ],
  });

  assert.deepEqual(first, [{
    timestamp: "2026-11-18T03:00:00+00:00",
    prices: { NIFTY26NOVFUT: 25000, NIFTY27JANFUT: 25100 },
  }]);
  assert.equal(appendLivePricePoint(first, {
    feed: { status: "fresh", last_tick_at: "2026-11-18T03:00:00+00:00" },
    futures_contracts: [{ tradingsymbol: "NIFTY26NOVFUT", price: 25001 }],
  }), first);
});

test("does not create chart points from stale or missing exchange timestamps", () => {
  const history = [{ timestamp: "2026-11-18T03:00:00+00:00", prices: { NIFTY26NOVFUT: 25000 } }];
  assert.equal(appendLivePricePoint(history, {
    feed: { status: "fresh", last_tick_at: null },
    futures_contracts: [{ tradingsymbol: "NIFTY26NOVFUT", price: 25001 }],
  }), history);
});

test("keeps only the newest configured number of real chart points", () => {
  const history = Array.from({ length: 3 }, (_, index) => ({
    timestamp: `2026-11-18T03:00:0${index}+00:00`,
    prices: { NIFTY26NOVFUT: 25000 + index },
  }));
  const next = appendLivePricePoint(history, {
    feed: { status: "fresh", last_tick_at: "2026-11-18T03:00:03+00:00" },
    futures_contracts: [{ tradingsymbol: "NIFTY26NOVFUT", price: 25003 }],
  }, 3);

  assert.deepEqual(next.map(point => point.prices.NIFTY26NOVFUT), [25001, 25002, 25003]);
});

test("does not chart stale exchange ticks as live price history", () => {
  const history = [];
  assert.equal(appendLivePricePoint(history, {
    feed: { status: "stale", last_tick_at: "2026-11-18T03:00:00+00:00" },
    futures_contracts: [{ tradingsymbol: "NIFTY26NOVFUT", price: 25000 }],
  }), history);
});

test("uses each contract exchange timestamp instead of the newest unrelated tick", () => {
  const result = appendLivePricePoint([], {
    feed: { status: "fresh", last_tick_at: "2026-11-18T03:00:05+00:00" },
    futures_contracts: [
      { tradingsymbol: "NIFTY26NOVFUT", price: 25000, exchange_timestamp: "2026-11-18T03:00:00+00:00" },
      { tradingsymbol: "NIFTY27JANFUT", price: 25100, exchange_timestamp: "2026-11-18T03:00:05+00:00" },
    ],
  });

  assert.deepEqual(result, [
    { timestamp: "2026-11-18T03:00:00+00:00", prices: { NIFTY26NOVFUT: 25000 } },
    { timestamp: "2026-11-18T03:00:05+00:00", prices: { NIFTY27JANFUT: 25100 } },
  ]);
});
