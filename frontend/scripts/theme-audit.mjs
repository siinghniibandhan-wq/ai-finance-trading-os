import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
const css = readFileSync(new URL("../src/visual-design.css", import.meta.url), "utf8");
const themeTokens = readFileSync(new URL("../src/theme-unify.css", import.meta.url), "utf8");
const componentSystem = readFileSync(new URL("../src/theme-component-system.css", import.meta.url), "utf8");
const main = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");

const expectedThemes = [
  "Default", "Light", "Dark", "Skeuomorphism", "Neumorphism",
  "Brutalism", "Retro Terminal", "Elegant Plain", "Bento Grid",
  "Nordic", "Editorial",
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
for (const slug of slugs) {
  assert.ok(themeTokens.includes(`data-finos-theme="${slug}"`), `Missing central palette for theme: ${slug}`);
}
console.log(`PASS: all ${slugs.length} themes have central palette definitions.`);

for (const token of [
  "--th-surface-raised", "--th-surface-inset", "--th-tab-bg", "--th-tab-text",
  "--th-tab-active-bg", "--th-tab-active-text", "--th-tab-border", "--th-tab-radius",
  "--th-button-primary-bg", "--th-button-primary-text", "--th-button-secondary-bg",
  "--th-button-secondary-text", "--th-input-surface", "--th-input-text",
  "--th-input-border", "--th-icon", "--th-icon-muted", "--th-focus",
  "--th-hover-surface", "--th-selected-surface", "--th-card-shadow",
]) {
  assert.ok(themeTokens.includes(token), `Missing semantic theme token: ${token}`);
}
for (const selector of ['.tax-centre nav[aria-label="Tax sections"] button', '.instrument-research-tab', '.instrument-chart-range-button', 'input', 'textarea', '.metric-icon']) {
  assert.ok(componentSystem.includes(selector), `Shared component styling missing: ${selector}`);
}
console.log("PASS: shared semantic component tokens and cross-module tab/form/icon rules exist.");

for (const token of [
  "--finos-text:var(--th-text)", "--finos-border:var(--th-border)",
  "--finos-accent:var(--th-accent)", "--t-card-bg:var(--th-card)",
  "--t-page-bg:var(--th-page)", "--finos-chart-series-1:var(--th-chart-1)",
]) {
  assert.ok(componentSystem.includes(token), `Legacy token bridge missing: ${token}`);
}
console.log("PASS: legacy --finos-* and --t-* tokens map to the central theme contract.");

const cssImports = [...main.matchAll(/import ["']\.\/[^"']+\.css["'];/g)].map((match) => match[0]);
assert.equal(cssImports.at(-1), 'import "./theme-component-system.css";', "Shared theme component contract must load after legacy styles.");
for (const removedTheme of ["Aurora", "Emerald", "Ocean", "Sunset", "Minimal", "Glass", "Claymorphism", "Maximalism", "Liquid Glass"]) {
  assert.ok(!themesDeclaration[1].includes(`"${removedTheme}"`), `Removed theme must not remain selectable: ${removedTheme}`);
}
console.log("PASS: the central component contract loads last and retired themes are absent from the selector.");



function parseHexColor(hex) {
  const raw = hex.replace("#", "");
  const expanded = raw.length === 3 ? [...raw].map((part) => part + part).join("") : raw;
  if (!/^[0-9a-fA-F]{6}$/.test(expanded)) return null;
  return [0, 2, 4].map((offset) => parseInt(expanded.slice(offset, offset + 2), 16) / 255);
}
function relativeLuminance(hex) {
  const channels = parseHexColor(hex);
  if (!channels) return null;
  const linear = channels.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}
function contrastRatio(first, second) {
  const a = relativeLuminance(first);
  const b = relativeLuminance(second);
  if (a === null || b === null) return null;
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
for (const slug of slugs) {
  const declaration = themeTokens.match(new RegExp(`\\[data-finos-theme=["']${slug}["']\\]\\{([^}]*)\\}`));
  assert.ok(declaration, `Theme palette not found for contrast check: ${slug}`);
  const colour = (name) => declaration[1].match(new RegExp(`--th-${name}:(#[0-9a-fA-F]{3,6})(?![0-9a-fA-F])`))?.[1];
  const page = colour("page");
  const card = colour("card");
  const text = colour("text");
  const muted = colour("muted");
  const accent = colour("accent");
  const onAccent = colour("on-accent");
  assert.ok([page, card, text, muted, accent, onAccent].every(Boolean), `Missing contrast-critical palette value for ${slug}`);
  assert.ok(contrastRatio(text, page) >= 4.5, `${slug}: primary text/page contrast must be at least 4.5:1`);
  assert.ok(contrastRatio(text, card) >= 4.5, `${slug}: primary text/card contrast must be at least 4.5:1`);
  assert.ok(contrastRatio(muted, card) >= 4.5, `${slug}: muted text/card contrast must be at least 4.5:1`);
  assert.ok(contrastRatio(onAccent, accent) >= 4.5, `${slug}: accent button text contrast must be at least 4.5:1`);
  assert.ok(contrastRatio(accent, card) >= 3, `${slug}: accent/icon contrast must be at least 3:1`);
}
console.log(`PASS: all ${slugs.length} theme palettes meet the defined text and accent contrast checks.`);



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

console.log("NOTE: These are static regression checks; they do not replace real-browser visual/accessibility testing.");
