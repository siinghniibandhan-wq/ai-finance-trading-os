import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const component = readFileSync(new URL("./FlowDiagram.jsx", import.meta.url), "utf8");
const css = readFileSync(new URL("./order-flow.css", import.meta.url), "utf8");

test("Order Flow renders the continuous chart-to-gate-to-card diagram", () => {
  for (const feature of ["mf-faithful-svg", "mf-gate-shell", "mf-zero-spine", "mf-gate-branch", "mf-card-joint"]) {
    assert.ok(component.includes(feature), `missing diagram element: ${feature}`);
  }
});

test("Order Flow includes stock tiles, featured cards and strike-level option OI", () => {
  assert.match(component, /kind="tall"/);
  assert.match(component, /kind="card"/);
  assert.match(component, /stock\.strikes/);
  assert.match(component, /mf-node-spark/);
});

test("Order Flow diagram supports responsive sizing, selection and sector focus", () => {
  assert.match(component, /ResizeObserver/);
  assert.match(component, /onPointerMove/);
  assert.match(component, /onPin\(stock\.symbol\)/);
  assert.match(component, /selectedSector/);
  assert.match(css, /\.mf-faithful-diagram/);
  assert.match(css, /prefers-reduced-motion/);
});
