import test from "node:test";
import assert from "node:assert/strict";
import { createMarketOverviewStore } from "./marketOverviewStore.js";

const snapshot = (gainer = "RELIANCE") => ({
  status: "success",
  indices: [{ name: "NIFTY 50", last_price: 25000 }],
  market_movers: {
    gainers: [{ symbol: gainer, exchange: "NSE", ltp: 100, percent_change: 1 }],
    losers: [{ symbol: "TCS", exchange: "NSE", ltp: 200, percent_change: -1 }],
  },
  errors: [],
  last_updated: "2026-11-19T10:00:00Z",
});

test("concurrent Market and Order Flow consumers share one in-flight refresh and snapshot", async () => {
  let calls = 0;
  let resolveFetch;
  const store = createMarketOverviewStore(() => {
    calls += 1;
    return new Promise((resolve) => { resolveFetch = resolve; });
  });
  const marketUpdates = [];
  const flowUpdates = [];
  store.subscribe(() => marketUpdates.push(store.getSnapshot()));
  store.subscribe(() => flowUpdates.push(store.getSnapshot()));

  const marketRequest = store.refresh();
  const flowRequest = store.refresh();
  assert.equal(calls, 0, "fetch begins in the next microtask");
  await Promise.resolve();
  assert.equal(calls, 1);
  resolveFetch(snapshot());
  await Promise.all([marketRequest, flowRequest]);

  assert.equal(store.getSnapshot().data.market_movers.gainers[0].symbol, "RELIANCE");
  assert.ok(marketUpdates.length > 0);
  assert.ok(flowUpdates.length > 0);
});

test("a total provider failure retains the last successful market snapshot", async () => {
  let response = snapshot("INFY");
  const store = createMarketOverviewStore(async () => response);
  await store.refresh();
  response = { status: "error", indices: [], market_movers: { gainers: [], losers: [] }, errors: [{ source: "market_movers" }] };
  await store.refresh();

  assert.equal(store.getSnapshot().data.market_movers.gainers[0].symbol, "INFY");
  assert.match(store.getSnapshot().error, /last successful snapshot is retained/i);
});

test("partial refreshes retain failed mover sections for both consumers", async () => {
  let response = snapshot("HDFC");
  const store = createMarketOverviewStore(async () => response);
  await store.refresh();
  response = {
    ...snapshot("ICICI"),
    status: "partial",
    market_movers: { gainers: [{ symbol: "ICICI", exchange: "NSE", ltp: 50, percent_change: 2 }], losers: [] },
    errors: [{ source: "market_movers", type: "losers", message: "timeout" }],
  };
  await store.refresh();

  assert.equal(store.getSnapshot().data.market_movers.gainers[0].symbol, "ICICI");
  assert.equal(store.getSnapshot().data.market_movers.losers[0].symbol, "TCS");
  assert.equal(store.getSnapshot().data.stale_sections.losers, true);
});
