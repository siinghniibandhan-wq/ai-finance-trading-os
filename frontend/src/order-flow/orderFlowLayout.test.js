import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("./order-flow.css", import.meta.url), "utf8");

test("Order Flow responds to its available workspace width, not only device width", () => {
  assert.match(css, /\.market-flow-workspace\s*\{[^}]*container-type:\s*inline-size/s);
  assert.match(css, /@container\s*\([^)]*max-width:\s*\d+px\)/);
});

test("narrow desktop workspace keeps the chart and sector rail usable", () => {
  assert.match(css, /@container\s*\([^)]*max-width:\s*\d+px\)[\s\S]*?\.mf-board\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*\d+px\)\s+minmax\(0,\s*1fr\)/);
  assert.match(css, /\.mf-sector-rail\s*\{[^}]*max-height:/);
  assert.match(css, /\.mf-chart-panel\s*\{[^}]*min-height:/);
});

test("narrow desktop cards and detail metrics avoid three-column micro tiles", () => {
  assert.match(css, /\.mf-tiles\s*\{[^}]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\)/);
  assert.match(css, /\.mf-detail-metrics\s*\{[^}]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\)/);
});
