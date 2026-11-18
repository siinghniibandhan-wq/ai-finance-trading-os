import test from "node:test";
import assert from "node:assert/strict";
import { normalizeMoverRows, summarizeMoverRows } from "./marketScannerModel.js";

test("normalizes provider mover rows without inventing prices or exchanges", () => {
  const rows = normalizeMoverRows([
    { symbol: "RELIANCE", exchange: "NSE", ltp: "1250.5", percent_change: "-2.5", volume: "900" },
    { symbol: "TCS", exchange: "BSE", ltp: 3500, percent_change: "-1.25" },
    { symbol: "BAD", ltp: 100, percent_change: -4 },
    { symbol: "ZERO", exchange: "NSE", ltp: 0, percent_change: -1 },
    { symbol: "INVALID", exchange: "NSE", ltp: 12, percent_change: "NaN" },
  ]);
  assert.deepEqual(rows.map(({ symbol, exchange, lastPrice, changePercent }) => ({
    symbol, exchange, lastPrice, changePercent,
  })), [
    { symbol: "RELIANCE", exchange: "NSE", lastPrice: 1250.5, changePercent: -2.5 },
    { symbol: "TCS", exchange: "BSE", lastPrice: 3500, changePercent: -1.25 },
  ]);
});

test("sorts the scanner by largest absolute provider percentage move", () => {
  const rows = normalizeMoverRows([
    { symbol: "A", exchange: "NSE", ltp: 10, percent_change: -1 },
    { symbol: "B", exchange: "NSE", ltp: 20, percent_change: -5 },
    { symbol: "C", exchange: "NSE", ltp: 30, percent_change: -3 },
  ]);
  assert.deepEqual(rows.map((row) => row.symbol), ["B", "C", "A"]);
});

test("filters out rows whose provider movement contradicts the requested scanner", () => {
  assert.deepEqual(normalizeMoverRows([
    { symbol: "UP", exchange: "NSE", ltp: 10, percent_change: 1 },
    { symbol: "DOWN", exchange: "NSE", ltp: 10, percent_change: -1 },
  ], "losers").map((row) => row.symbol), ["DOWN"]);
  assert.deepEqual(normalizeMoverRows([
    { symbol: "UP", exchange: "NSE", ltp: 10, percent_change: 1 },
    { symbol: "DOWN", exchange: "NSE", ltp: 10, percent_change: -1 },
  ], "gainers").map((row) => row.symbol), ["UP"]);
});

test("summarizes only validated provider rows and preserves unavailable volume", () => {
  const summary = summarizeMoverRows(normalizeMoverRows([
    { symbol: "A", exchange: "NSE", ltp: 10, percent_change: -2, volume: 100 },
    { symbol: "B", exchange: "BSE", ltp: 20, percent_change: -1 },
  ]));
  assert.deepEqual(summary, { count: 2, averageChangePercent: -1.5, totalReportedVolume: 100, rowsWithVolume: 1 });
});

test("returns an empty scanner for malformed provider payloads", () => {
  assert.deepEqual(normalizeMoverRows(null), []);
  assert.deepEqual(normalizeMoverRows({ movers: [] }), []);
});
