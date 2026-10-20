import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
const css = readFileSync(new URL("../src/visual-design.css", import.meta.url), "utf8");
const tokens = readFileSync(new URL("../src/theme-tokens.css", import.meta.url), "utf8");
const main = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");

const expectedThemes = [
  "Default", "Light", "Dark", "Aurora", "Emerald", "Ocean", "Sunset",
  "Minimal", "Retro Terminal", "Skeuomorphism", "Neumorphism",
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
  assert.ok(tokens.includes(token), `Missing theme token: ${token}`);
}
console.log(`PASS: all ${requiredTokens.length} shared chart/control tokens exist.`);

for (const slug of slugs) {
  const selector = new RegExp(`data-finos-theme=["']${slug}["']`);
  assert.ok(selector.test(tokens), `No theme-specific CSS selector found for ${slug}`);
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

// BUY/SELL regression guards: these static checks catch accidental removal of
// the Market-to-Portfolio intent matcher and transaction form safety checks.
assert.ok(
  /replace\(\/\\s\+\/g, " "\)/.test(app),
  "BUY/SELL instrument normalization must collapse whitespace correctly",
);
assert.ok(
  /if \(transactionLoading \|\| !transactionModal\?\.investment\)/.test(app),
  "BUY/SELL submission must ignore duplicate saves and missing investments",
);
assert.ok(
  app.includes("Fees must be a valid amount greater than or equal to zero."),
  "BUY/SELL form must reject invalid or negative fees",
);
assert.ok(
  app.includes("Quantity and price must be valid numbers."),
  "BUY/SELL form must reject non-finite quantity and price values",
);
assert.ok(
  /if \(!editingInvestmentId\) \{[\s\S]{0,500}transaction_type:\s*"BUY"/.test(app),
  "Creating a new Portfolio investment must create its initial BUY transaction only in create mode",
);
assert.ok(
  app.includes("This instrument is not in your portfolio, so there is no holding to sell."),
  "SELL on an instrument without a holding must show clear feedback",
);
console.log("PASS: BUY/SELL intent matching, validation, initial BUY, and no-holding guards exist.");


assert.ok(!themesDeclaration[1].includes('"Glass"'), "Deprecated Glass theme must not be registered");
assert.ok(!app.includes('"Glass":'), "Deprecated Glass theme description must not remain");
assert.ok(app.includes("18 visual styles."), "Theme gallery must display the correct count of 18");
console.log("PASS: deprecated Glass theme is removed and gallery count is 18.");

assert.ok(main.includes('import "./theme-tokens.css";'), "main.jsx must load the theme token contract");
assert.ok(main.includes('import "./theme-components.css";'), "main.jsx must load shared token-based component styles");
assert.ok(!main.includes('import "./instrument-interaction-contrast.css";'), "Deprecated instrument contrast stylesheet import remains");
assert.ok(!main.includes('import "./holdings-dark-cards.css";'), "Deprecated holdings stylesheet import remains");
assert.ok(/replace\(\/\\s\+\/g, "-"/.test(main), "Saved theme slug must normalize whitespace");
console.log("PASS: startup theme tokens, deprecated stylesheet imports, and saved theme slug are checked.");


console.log("NOTE: These are static regression checks; they do not replace real-browser visual/accessibility testing.");
