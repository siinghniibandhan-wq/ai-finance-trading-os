import test from "node:test";
import assert from "node:assert/strict";
import * as flowLayout from "./flowBoardLayout.js";
import { getFlowBoardLayout } from "./flowBoardLayout.js";

test("uses the continuous full-width diagram on wide desktop workspaces",()=>{
 const layout=getFlowBoardLayout(1800,900);
 assert.equal(layout.mode,"diagram");
 assert.ok(layout.columns.chart>0);
 assert.ok(layout.columns.cards>0);
 assert.ok(layout.columns.chart+layout.columns.gate+layout.columns.tiles+layout.columns.cards<=1800);
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
test("keeps every bullish and bearish fan curve inside the chart viewport",()=>{
 for(const side of ["bullish","bearish"]){
  for(let index=0;index<8;index++){
   const point=flowLayout.getFlowFanCoordinates(side,index);
   assert.ok(point.y0>=0&&point.y0<=100,side+" start is visible");
   assert.ok(point.y1>=0&&point.y1<=100,side+" end is visible");
  }
 }
});
test("mirrors bearish fan direction into the lower half of the chart",()=>{
 const bullish=flowLayout.getFlowFanCoordinates("bullish",0);
 const bearish=flowLayout.getFlowFanCoordinates("bearish",0);
 assert.ok(bullish.y0>bullish.y1);
 assert.ok(bearish.y0<bearish.y1);
});
