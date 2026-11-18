import test from "node:test";
import assert from "node:assert/strict";
import { normalizeCandles } from "./model.js";

test("normalizes valid m.Stock OHLCV candles into sorted chart points", () => {
  const candles = [
    ["2026-11-18T09:20:00+05:30", 101, 104, 100, 103, 1200],
    ["2026-11-18T09:15:00+05:30", 99, 102, 98, 101, 900],
  ];
  assert.deepEqual(normalizeCandles(candles), [
    { time: Math.floor(Date.parse("2026-11-18T09:15:00+05:30") / 1000), open: 99, high: 102, low: 98, close: 101, volume: 900 },
    { time: Math.floor(Date.parse("2026-11-18T09:20:00+05:30") / 1000), open: 101, high: 104, low: 100, close: 103, volume: 1200 },
  ]);
});

test("normalizes the actual Market Charts API object response into sorted chart points", () => {
  const candles = [
    { timestamp: "2026-11-18T09:20:00+05:30", open: 101, high: 104, low: 100, close: 103, volume: 1200 },
    { timestamp: "2026-11-18T09:15:00+05:30", open: 99, high: 102, low: 98, close: 101, volume: 900 },
  ];
  assert.deepEqual(normalizeCandles(candles), [
    { time: Math.floor(Date.parse("2026-11-18T09:15:00+05:30") / 1000), open: 99, high: 102, low: 98, close: 101, volume: 900 },
    { time: Math.floor(Date.parse("2026-11-18T09:20:00+05:30") / 1000), open: 101, high: 104, low: 100, close: 103, volume: 1200 },
  ]);
});

test("drops malformed candles and rejects impossible OHLC ranges", () => {
  const candles = [
    ["2026-11-18T09:15:00+05:30", 100, 99, 98, 101, 20],
    ["bad-time", 100, 102, 98, 101, 20],
    ["2026-11-18T09:20:00+05:30", 100, 102, 98, 101, 20],
    ["2026-11-18T09:25:00+05:30", 100, 102, 98, 101, -1],
    { timestamp: "bad-time", open: 100, high: 102, low: 98, close: 101, volume: 20 },
    { timestamp: "2026-11-18T09:25:00+05:30", open: 100, high: 99, low: 98, close: 101, volume: 20 },
  ];
  assert.equal(normalizeCandles(candles).length, 1);
});

test("deduplicates timestamps and keeps the last valid candle", () => {
  const candles = [
    [1794973500, 100, 102, 99, 101, 10],
    [1794973500, 101, 104, 100, 103, 20],
  ];
  assert.deepEqual(normalizeCandles(candles), [
    { time: 1794973500, open: 101, high: 104, low: 100, close: 103, volume: 20 },
  ]);
});

test("returns an empty series for a non-array provider response", () => {
  assert.deepEqual(normalizeCandles(null), []);
});

test("keeps chart dimensions aligned with the responsive chart container", async () => {
  const { getChartDimensions } = await import("./model.js");
  assert.deepEqual(getChartDimensions(280, 360), { width: 320, height: 360 });
  assert.deepEqual(getChartDimensions(960, 430), { width: 960, height: 430 });
  assert.deepEqual(getChartDimensions(0, 0), { width: 320, height: 520 });
});

test("calculates a simple moving average from actual candle closes", async () => {
  const { calculateSMA } = await import("./model.js");
  const candles = [
    { time: 1, close: 10 },
    { time: 2, close: 12 },
    { time: 3, close: 14 },
    { time: 4, close: 16 },
  ];
  assert.deepEqual(calculateSMA(candles, 3), [
    { time: 3, value: 12 },
    { time: 4, value: 14 },
  ]);
});

test("calculates an exponential moving average seeded by the first period SMA", async () => {
  const { calculateEMA } = await import("./model.js");
  const candles = [
    { time: 1, close: 10 },
    { time: 2, close: 12 },
    { time: 3, close: 14 },
    { time: 4, close: 16 },
  ];
  assert.deepEqual(calculateEMA(candles, 3), [
    { time: 3, value: 12 },
    { time: 4, value: 14 },
  ]);
});

test("returns no moving-average points until a full period exists", async () => {
  const { calculateSMA, calculateEMA } = await import("./model.js");
  const candles = [{ time: 1, close: 10 }, { time: 2, close: 12 }];
  assert.deepEqual(calculateSMA(candles, 3), []);
  assert.deepEqual(calculateEMA(candles, 3), []);
});

test("formats Lightweight Charts business-day values without timezone conversion", async () => {
  const { formatChartTime } = await import("./model.js");
  assert.equal(formatChartTime({ year: 2026, month: 11, day: 19 }), "19/11/2026");
  assert.equal(formatChartTime(null), "—");
});


test("normalizes a real quote price for the chart last-price line", async () => {
  const { normalizeQuotePrice } = await import("./model.js");
  assert.equal(normalizeQuotePrice({ quote: { last_price: "123.45" } }), 123.45);
  assert.equal(normalizeQuotePrice({ quote: { last_price: 0 } }), null);
  assert.equal(normalizeQuotePrice({ quote: { last_price: "not-a-price" } }), null);
  assert.equal(normalizeQuotePrice(null), null);
});


test("builds instrument search parameters with an explicit supported exchange filter", async () => {
  const { buildInstrumentSearchParams } = await import("./model.js");
  assert.deepEqual(Object.fromEntries(buildInstrumentSearchParams("  reliance ", "NSE")), {
    query: "reliance", exchange: "NSE", limit: "20", product_type: "Stocks",
  });
  assert.equal(buildInstrumentSearchParams("TCS", "BSE").get("exchange"), "BSE");
  assert.equal(buildInstrumentSearchParams("TCS", "INVALID").get("exchange"), "ALL");
});


test("preserves valid OHLC candles when the provider does not supply volume", async () => {
  const { normalizeCandles } = await import("./model.js");
  assert.deepEqual(normalizeCandles([
    {
      timestamp: "2026-11-18T09:15:00+05:30",
      open: 100,
      high: 105,
      low: 99,
      close: 103,
      volume: null,
    },
  ]), [
    {
      time: Math.floor(Date.parse("2026-11-18T09:15:00+05:30") / 1000),
      open: 100,
      high: 105,
      low: 99,
      close: 103,
      volume: null,
    },
  ]);
});

test("normalizes numeric Unix timestamps supplied as strings", async () => {
  const { normalizeCandles } = await import("./model.js");
  assert.deepEqual(normalizeCandles([
    ["1794973500", 100, 102, 99, 101, 10],
  ]), [
    { time: 1794973500, open: 100, high: 102, low: 99, close: 101, volume: 10 },
  ]);
});

test("builds Heikin-Ashi candles from provider OHLC without changing source candles", async () => {
  const { calculateHeikinAshi } = await import("./model.js");
  const source = [
    { time: 1, open: 10, high: 14, low: 8, close: 12 },
    { time: 2, open: 12, high: 16, low: 10, close: 14 },
  ];
  assert.deepEqual(calculateHeikinAshi(source), [
    { time: 1, open: 11, high: 14, low: 8, close: 11 },
    { time: 2, open: 11, high: 16, low: 10, close: 13 },
  ]);
  assert.equal(source[0].open, 10);
});

test("returns no Heikin-Ashi data for malformed OHLC input", async () => {
  const { calculateHeikinAshi } = await import("./model.js");
  assert.deepEqual(calculateHeikinAshi([{ time: 1, open: 10, high: 9, low: 8, close: 11 }]), []);
});
