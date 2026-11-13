import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("./order-flow.css", import.meta.url), "utf8");

test("Order Flow surfaces and text use the shared active-theme tokens", () => {
  assert.match(css, /\.market-flow-workspace\s*\{[^}]*color:\s*var\(--th-text\)/s);
  assert.match(css, /\.market-flow-workspace\s*\{[^}]*background:\s*var\(--th-page\)/s);
  assert.match(css, /\.market-flow-workspace\s+:is\([^}]+\)\s*\{[^}]*color:\s*var\(--th-muted\)/s);
});

test("Order Flow cards, controls and chart use semantic theme surfaces and colors", () => {
  assert.match(css, /\.market-flow-workspace\s+:is\([^}]+\)\s*\{[^}]*background:\s*var\(--th-card\)/s);
  assert.match(css, /\.market-flow-workspace\s+:is\([^}]+\)\s*\{[^}]*border-color:\s*var\(--th-border\)/s);
  assert.match(css, /\.mf-chart\s*\{[^}]*--mf-up:\s*var\(--th-pos\)/s);
  assert.match(css, /\.mf-chart\s*\{[^}]*--mf-down:\s*var\(--th-neg\)/s);
});

test("theme-aware Order Flow rules cover SVG labels, buttons and selection states", () => {
  assert.match(css, /\.market-flow-workspace\s+\.mf-axis\s*\{[^}]*fill:\s*var\(--th-muted\)/s);
  assert.match(css, /\.market-flow-workspace\s+button\s*\{[^}]*color:\s*var\(--th-text\)/s);
  assert.match(css, /\.market-flow-workspace\s+\.is-selected\s*\{[^}]*background:\s*var\(--th-selected-surface\)/s);
});
