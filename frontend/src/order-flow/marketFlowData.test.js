import test from "node:test";
import assert from "node:assert/strict";
import { toSpotChangeRows } from "./marketFlowData.js";

test("calculates spot percentage change from spot and previous close", () => {
  assert.deepEqual(toSpotChangeRows([
    { s: "UP", sp: 110, pc: 100 },
    { s: "DOWN", sp: 90, pc: 100 },
  ]), [
    { symbol: "UP", change: 10 },
    { symbol: "DOWN", change: -10 },
  ]);
});

test("ignores rows without a valid previous close or symbol", () => {
  assert.deepEqual(toSpotChangeRows([
    { s: "ZERO", sp: 100, pc: 0 },
    { s: "MISSING", sp: 100 },
    { sp: 100, pc: 90 },
  ]), []);
});
