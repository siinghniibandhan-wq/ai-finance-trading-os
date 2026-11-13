import test from "node:test";
import assert from "node:assert/strict";
import { loadOrderFlowPreferences, saveOrderFlowPreferences } from "./marketFlowPreferences.js";

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
}

test("persists selected universe and instrument across workspace visits", () => {
  const storage = memoryStorage();
  assert.equal(saveOrderFlowPreferences({ scope: "nifty50", selectedSymbol: "INFY" }, storage), true);
  assert.deepEqual(loadOrderFlowPreferences(storage), { scope: "nifty50", selectedSymbol: "INFY" });
});

test("recovers safely from corrupt or unavailable browser storage", () => {
  assert.deepEqual(loadOrderFlowPreferences(memoryStorage({ "financial-os:order-flow-preferences:v1": "{" })), { scope: "fno", selectedSymbol: "NIFTY" });
  assert.equal(saveOrderFlowPreferences({ scope: "fno", selectedSymbol: "SBIN" }, { setItem() { throw new Error("blocked"); } }), false);
});
