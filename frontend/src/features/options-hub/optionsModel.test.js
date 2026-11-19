import test from "node:test";
import assert from "node:assert/strict";
import { buildOptionChainRows, calculateOptionsAnalytics, buildOptionOIBars } from "./optionsModel.js";

const completeChain = [
  { strike: 100, side: "CE", last_price: 12, volume: 100, open_interest: 1000, quote_available: true },
  { strike: 100, side: "PE", last_price: 8, volume: 120, open_interest: 800, quote_available: true },
  { strike: 110, side: "CE", last_price: 7, volume: 90, open_interest: 600, quote_available: true },
  { strike: 110, side: "PE", last_price: 14, volume: 110, open_interest: 1400, quote_available: true },
  { strike: 120, side: "CE", last_price: 3, volume: 80, open_interest: 300, quote_available: true },
  { strike: 120, side: "PE", last_price: 23, volume: 70, open_interest: 1800, quote_available: true },
];

test("normalizes provider CE/PE contracts into sorted strike rows", () => {
  const rows = buildOptionChainRows([...completeChain].reverse());
  assert.deepEqual(rows.map(row => row.strike), [100, 110, 120]);
  assert.equal(rows[0].CE.lastPrice, 12);
  assert.equal(rows[2].PE.openInterest, 1800);
});

test("does not invent missing contracts or quote fields", () => {
  const rows = buildOptionChainRows([
    { strike: 100, side: "CE", last_price: null, open_interest: null },
    { strike: 110, side: "XX", last_price: 1, open_interest: 10 },
    { strike: 120, side: "PE", last_price: 5, open_interest: 0 },
  ]);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].CE.lastPrice, null);
  assert.equal(rows[0].PE, null);
});

test("calculates PCR and Max Pain only with complete two-sided OI", () => {
  const result = calculateOptionsAnalytics(completeChain);
  assert.equal(result.oiComplete, true);
  assert.equal(result.callOI, 1900);
  assert.equal(result.putOI, 4000);
  assert.equal(result.pcr, 4000 / 1900);
  assert.equal(result.maxPain, 120);
});

test("withholds PCR and Max Pain when any strike side or OI is missing", () => {
  const partial = calculateOptionsAnalytics([
    { strike: 100, side: "CE", open_interest: 10 },
    { strike: 100, side: "PE", open_interest: 20 },
    { strike: 110, side: "CE", open_interest: 5 },
    { strike: 110, side: "PE", open_interest: null },
  ]);
  assert.equal(partial.oiComplete, false);
  assert.equal(partial.pcr, null);
  assert.equal(partial.maxPain, null);
});

test("builds mirrored OI bars only from complete provider observations", () => {
  const result = calculateOptionsAnalytics(completeChain);
  const bars = buildOptionOIBars(result.rows, 100);
  assert.equal(bars.length, 3);
  assert.equal(Math.max(...bars.map(row => row.callWidth)), 100 * 1000 / 1800);
  assert.equal(Math.max(...bars.map(row => row.putWidth)), 100);
  assert.equal(buildOptionOIBars([]).length, 0);
});
