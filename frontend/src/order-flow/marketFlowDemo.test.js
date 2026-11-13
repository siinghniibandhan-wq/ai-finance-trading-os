import test from "node:test";
import assert from "node:assert/strict";
import { buildDemoFlow } from "./marketFlowDemo.js";

test("builds deterministic, clearly separated Nifty 50 and F&O universes",()=>{
 const nifty=buildDemoFlow("nifty50"),all=buildDemoFlow("fno");
 assert.equal(nifty.stocks.length,51);
 assert.equal(all.stocks.length,217);
 assert.ok(nifty.stocks.some(s=>s.symbol==="NIFTY"));
 assert.ok(nifty.stocks.every(s=>["bullish","bearish","rangebound"].includes(s.side)));
});
test("classifies every underlying exactly once and supplies option positioning",()=>{
 const flow=buildDemoFlow("fno"),classified=[...flow.bullish,...flow.bearish,...flow.stocks.filter(s=>s.side==="rangebound")];
 assert.equal(classified.length,flow.stocks.length);
 assert.equal(new Set(classified.map(s=>s.symbol)).size,flow.stocks.length);
 for(const s of flow.stocks){assert.ok(s.oi>0);assert.ok(s.strikes.length>0);assert.ok(s.support>0);assert.ok(s.resistance>0);assert.ok(s.candles.length===76)}
});
test("keeps simulated data stable across repeated builds",()=>{
 assert.deepEqual(buildDemoFlow("nifty50").stocks,buildDemoFlow("nifty50").stocks);
});

test("steps through a side list without wrapping or losing the selected symbol", async()=>{
 const { adjacentStock } = await import("./marketFlowDemo.js");
 const items=[{symbol:"AAA"},{symbol:"BBB"},{symbol:"CCC"}];
 assert.equal(adjacentStock(items,"BBB",-1).symbol,"AAA");
 assert.equal(adjacentStock(items,"BBB",1).symbol,"CCC");
 assert.equal(adjacentStock(items,"AAA",-1),null);
 assert.equal(adjacentStock(items,"CCC",1),null);
 assert.equal(adjacentStock(items,"MISSING",1),null);
});
