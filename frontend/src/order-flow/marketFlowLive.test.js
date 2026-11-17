import test from "node:test";
import assert from "node:assert/strict";
import { buildLiveMarketView, getMarketFlowStatus, formatMarketValue } from "./marketFlowLive.js";

test("live status requires fresh tick and ready coverage", () => {
  assert.equal(getMarketFlowStatus({feed:{status:"fresh"},coverage:{state:"ready"},stream:{authenticated:true}}), "LIVE");
});
test("stale feed is not labelled live", () => {
  assert.equal(getMarketFlowStatus({feed:{status:"stale"},coverage:{state:"ready"}}), "STALE");
});
test("starting and auth-required coverage map to safe states", () => {
  assert.equal(getMarketFlowStatus({coverage:{state:"starting"}}), "CONNECTING");
  assert.equal(getMarketFlowStatus({coverage:{state:"auth_required"}}), "OFFLINE");
});
test("live view derives PCR and max OI levels without fabricated values", () => {
  const view = buildLiveMarketView({
    futures_contracts:[{symbol:"NIFTY",expiry:"2026-11-26",tradingsymbol:"NIFTY26NOVFUT",price:25000,oi:1200,volume:10}],
    option_oi_by_strike:[
      {strike:24900,ce_oi:100,pe_oi:300},
      {strike:25000,ce_oi:500,pe_oi:200}
    ],
    coverage:{unavailable:[{tradingsymbol:"NIFTY26DEC FUT",reason:"no tick received"}]},
    feed:{last_tick_at:"2026-11-17T09:20:00+00:00"}
  });
  assert.equal(view.futures[0].price,25000);
  assert.equal(view.pcr,1);
  assert.deepEqual(view.support,{strike:24900,oi:300});
  assert.deepEqual(view.resistance,{strike:25000,oi:500});
  assert.equal(view.unavailable.length,1);
});
test("missing price and OI remain unavailable, not zero", () => {
  const view = buildLiveMarketView({
    futures_contracts:[{symbol:"NIFTY",expiry:"2026-11-26",price:null,oi:null,volume:null}],
    option_oi_by_strike:[],
    coverage:{unavailable:[]}
  });
  assert.equal(view.futures[0].price,null);
  assert.equal(view.futures[0].oi,null);
  assert.equal(view.pcr,null);
  assert.equal(view.support,null);
  assert.equal(formatMarketValue(view.futures[0].price),"Unavailable");
});
