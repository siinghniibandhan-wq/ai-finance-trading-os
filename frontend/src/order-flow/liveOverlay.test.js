import test from "node:test";
import assert from "node:assert/strict";
import { overlayLiveData, isFreshSnapshot, nearestFutures, countLive } from "./liveOverlay.js";

const demo = () => [
  { symbol: "NIFTY", future: 1, oi: 2, changePct: 0.9, strikes: [{ strike: 1, call: 1, put: 1 }] },
  { symbol: "TCS", future: 5, oi: 6, changePct: -0.7, strikes: [] },
];
const snap = (over = {}) => ({
  status: "success", feed: { status: "fresh" },
  futures_contracts: [
    { symbol: "NIFTY", tradingsymbol: "NIFTY26DECFUT", expiry: "2026-12-29", price: 25000, volume: 900, oi: 123 },
    { symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT", expiry: "2026-11-24", price: 24950, volume: 800, oi: 100 },
  ],
  option_oi_by_strike: [{ strike: 25100, ce_oi: 10, pe_oi: 20 }, { strike: 25000, ce_oi: 30, pe_oi: 40 }],
  ...over,
});

test("fresh snapshot replaces price, oi, volume with nearest expiry", () => {
  const out = overlayLiveData(demo(), snap(), "NIFTY");
  assert.equal(out[0].future, 24950);
  assert.equal(out[0].oi, 100);
  assert.equal(out[0].liveVolume, 800);
  assert.equal(out[0].live, true);
});
test("change %, candles-driven fields are never touched", () => {
  const out = overlayLiveData(demo(), snap(), "NIFTY");
  assert.equal(out[0].changePct, 0.9);
});
test("option strikes only for the requested symbol, sorted, put/call mapped", () => {
  const out = overlayLiveData(demo(), snap(), "NIFTY");
  assert.deepEqual(out[0].strikes, [{ strike: 25000, call: 30, put: 40 }, { strike: 25100, call: 10, put: 20 }]);
  assert.equal(out[0].strikesLive, true);
  assert.equal(out[1].live, undefined);
  assert.deepEqual(out[1].strikes, []);
});
test("stale, disconnected, missing or failed snapshot leaves demo untouched", () => {
  const d = demo();
  for (const s of [null, undefined, snap({ feed: { status: "stale" } }), snap({ feed: { status: "disconnected" } }), snap({ status: "error" })]) {
    assert.equal(overlayLiveData(d, s, "NIFTY"), d);
  }
});
test("invalid prices and malformed rows are ignored", () => {
  const s = snap({ futures_contracts: [{ symbol: "TCS", price: 0, oi: 1 }, { symbol: "TCS", price: "x" }, null], option_oi_by_strike: [{ strike: 1 }] });
  const out = overlayLiveData(demo(), s, "TCS");
  assert.equal(out[1].live, undefined);
  assert.equal(out[1].strikesLive, undefined);
});
test("helpers", () => {
  assert.equal(isFreshSnapshot(snap()), true);
  assert.equal(nearestFutures(snap()).get("NIFTY").contract, "NIFTY26NOVFUT");
  assert.equal(countLive(overlayLiveData(demo(), snap(), "NIFTY")), 1);
});
