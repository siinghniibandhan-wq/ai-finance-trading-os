import test from "node:test";
import assert from "node:assert/strict";
import { calculateRSI, calculateATR, calculateBollingerBands, calculateMACD, calculateVWAP } from "./indicators.js";

const candles = [
  { time: 1, open: 10, high: 12, low: 9, close: 11, volume: 100 },
  { time: 2, open: 11, high: 13, low: 10, close: 12, volume: 200 },
  { time: 3, open: 12, high: 14, low: 11, close: 13, volume: 300 },
  { time: 4, open: 13, high: 15, low: 12, close: 14, volume: 400 },
  { time: 5, open: 14, high: 16, low: 13, close: 15, volume: 500 },
];

test("RSI uses actual closes and waits for a complete lookback", () => {
  assert.deepEqual(calculateRSI(candles, 3), [
    { time: 4, value: 100 },
    { time: 5, value: 100 },
  ]);
  assert.deepEqual(calculateRSI(candles.slice(0, 2), 3), []);
});

test("ATR uses true range including the previous close gap", () => {
  const values = calculateATR([
    { time: 1, high: 12, low: 10, close: 11 },
    { time: 2, high: 15, low: 13, close: 14 },
    { time: 3, high: 16, low: 14, close: 15 },
  ], 2);
  assert.deepEqual(values, [
    { time: 2, value: 3.5 },
    { time: 3, value: 2.75 },
  ]);
});

test("Bollinger bands use population standard deviation over actual closes", () => {
  const bands = calculateBollingerBands(candles, 3, 2);
  assert.equal(bands.length, 3);
  assert.equal(bands[0].time, 3);
  assert.ok(bands[0].upper > bands[0].middle);
  assert.ok(bands[0].lower < bands[0].middle);
});

test("MACD returns aligned MACD, signal and histogram points", () => {
  const result = calculateMACD(candles, 2, 3, 2);
  assert.equal(result.length, 2);
  assert.deepEqual(Object.keys(result[0]), ["time", "macd", "signal", "histogram"]);
});

test("VWAP skips missing or zero volume instead of inventing a weighted price", () => {
  const result = calculateVWAP([
    { time: 1, high: 12, low: 10, close: 11, volume: 100 },
    { time: 2, high: 13, low: 11, close: 12, volume: null },
    { time: 3, high: 14, low: 12, close: 13, volume: 300 },
  ]);
  assert.deepEqual(result, [
    { time: 1, value: 11 },
    { time: 3, value: 12.5 },
  ]);
});

test("indicator calculations reject invalid periods and malformed source rows", () => {
  assert.deepEqual(calculateRSI(candles, 0), []);
  assert.deepEqual(calculateATR([{ time: 1, high: 10, low: 11, close: 9 }], 1), []);
  assert.deepEqual(calculateVWAP([{ time: 1, high: 10, low: 9, close: 10, volume: -1 }]), []);
});
