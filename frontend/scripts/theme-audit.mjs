import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
const css = readFileSync(new URL("../src/visual-design.css", import.meta.url), "utf8");

const expectedThemes = [
  "Default", "Light", "Dark", "Aurora", "Emerald", "Ocean", "Sunset",
  "Minimal", "Retro Terminal", "Glass", "Skeuomorphism", "Neumorphism",
  "Glassmorphism", "Claymorphism", "Brutalism", "Maximalism",
  "Liquid Glass", "Bento Grid", "Elegant Plain",
];
const slugs = expectedThemes.map((theme) => theme.toLowerCase().replaceAll(" ", "-"));

const themesDeclaration = app.match(/const FINOS_THEMES = \[(.*?)\];/s);
assert.ok(themesDeclaration, "App.jsx must declare FINOS_THEMES");
for (const theme of expectedThemes) {
  assert.ok(themesDeclaration[1].includes(`"${theme}"`), `Theme missing from app: ${theme}`);
}
console.log(`PASS: all ${expectedThemes.length} expected themes are registered.`);

const requiredTokens = [
  "--finos-control-bg", "--finos-control-text", "--finos-control-muted",
  "--finos-control-border", "--finos-chart-bg", "--finos-chart-text",
  "--finos-chart-muted", "--finos-chart-grid", "--finos-chart-series-1",
  "--finos-chart-series-2", "--finos-chart-series-3", "--finos-chart-series-4",
  "--finos-chart-series-5",
];
for (const token of requiredTokens) {
  assert.ok(css.includes(token), `Missing theme token: ${token}`);
}
console.log(`PASS: all ${requiredTokens.length} shared chart/control tokens exist.`);

for (const slug of slugs) {
  const selector = new RegExp(`data-finos-theme=["']${slug}["']`);
  assert.ok(selector.test(css), `No theme-specific CSS selector found for ${slug}`);
}
console.log(`PASS: CSS includes theme-specific rules for all ${slugs.length} theme slugs.`);

for (const selector of [
  ".finos-select-menu", ".finos-select-option",
  ".wc-chart-surface", ".wc-periods", ".wc-chart-types",
  ".finos-theme-settings-grid", ".finos-theme-option",
]) {
  assert.ok(css.includes(selector), `Expected styled component selector missing: ${selector}`);
}
assert.ok(css.includes("@media (max-width: 760px)"), "Missing tablet/mobile theme gallery breakpoint");
assert.ok(css.includes("@media (max-width: 420px)"), "Missing narrow mobile theme gallery breakpoint");
assert.ok(css.includes("prefers-reduced-motion"), "Reduced-motion support should remain available");
console.log("PASS: dropdown, chart, theme gallery, mobile breakpoint, and reduced-motion rules exist.");

const braceBalance = (css.match(/{/g) || []).length - (css.match(/}/g) || []).length;
assert.equal(braceBalance, 0, "CSS braces must be balanced");
console.log("PASS: CSS brace balance is zero.");
console.log("NOTE: These are static regression checks; they do not replace real-browser visual/accessibility testing.");
