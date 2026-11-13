import test from "node:test";
import assert from "node:assert/strict";
import { getFlowBoardLayout } from "./flowBoardLayout.js";

test("uses the continuous full-width diagram on wide desktop workspaces",()=>{
 const layout=getFlowBoardLayout(1800,900);
 assert.equal(layout.mode,"diagram");
 assert.ok(layout.columns.diagram>0);
 assert.ok(layout.columns.cards>0);
 assert.ok(layout.columns.diagram+layout.columns.cards<=1800);
});
test("switches to split desktop, stacked tablet and switchable mobile panels",()=>{
 assert.equal(getFlowBoardLayout(1300,850).mode,"split");
 assert.equal(getFlowBoardLayout(900,800).mode,"stacked");
 assert.equal(getFlowBoardLayout(600,800).mode,"mobile");
});
test("keeps all column widths positive in compact and unusually wide viewports",()=>{
 for(const [width,height] of [[320,640],[760,900],[1100,700],[1680,900],[2560,1200]]){
  const layout=getFlowBoardLayout(width,height);
  assert.ok(Object.values(layout.columns).every(value=>Number.isFinite(value)&&value>=0));
 }
});
