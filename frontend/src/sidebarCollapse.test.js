import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const app = await readFile(new URL("./App.jsx", import.meta.url), "utf8");
const styles = await readFile(new URL("./styles.css", import.meta.url), "utf8");

test("desktop sidebar exposes an accessible collapse and expand control", () => {
  assert.match(app, /aria-label=\{sidebarCollapsed \? "Expand navigation sidebar" : "Collapse navigation sidebar"\}/);
  assert.match(app, /aria-controls="financial-os-sidebar"/);
  assert.match(app, /setSidebarCollapsed\(\(collapsed\) => !collapsed\)/);
});

test("collapsed state is applied at the app shell without changing page routing", () => {
  assert.match(app, /className=\{\`app-shell \$\{sidebarCollapsed \? "sidebar-collapsed" : ""\}\`\}/);
  assert.match(app, /const handleNavigation = \(page\) =>/);
  assert.match(app, /window\.history\.pushState\(\{ page: nextPage \}/);
});

test("compact sidebar layout is desktop-only and keeps navigation icons", () => {
  const desktopRules = styles.slice(styles.lastIndexOf("@media (min-width: 801px)"));
  assert.match(desktopRules, /\.app-shell\.sidebar-collapsed \.sidebar\s*\{[\s\S]*?width: 88px;/);
  assert.match(desktopRules, /\.app-shell\.sidebar-collapsed \.sidebar \.navigation-item\s*\{[\s\S]*?justify-content: center;/);
  assert.match(desktopRules, /\.app-shell\.sidebar-collapsed \.main-area\s*\{[\s\S]*?margin-left: 88px;/);
});

test("collapse control is hidden by default and enabled only on desktop", () => {
  assert.match(styles, /\.sidebar-collapse-toggle\s*\{[\s\S]*?display: none;/);
  assert.match(styles, /@media \(min-width: 801px\)\s*\{[\s\S]*?\.sidebar-collapse-toggle \{ display: inline-flex; \}/);
});

test("mobile close control remains available and mobile layout is not collapsed", () => {
  assert.match(app, /className="mobile-close"/);
  assert.match(styles, /@media \(max-width: 800px\)\s*\{\s*\.mobile-close \{ display: inline-flex; \}/);
  assert.doesNotMatch(styles, /@media \(max-width: 800px\)\s*\{[^}]*sidebar-collapsed/);
});


test("desktop sidebar uses a deliberate eased motion curve", () => {
  const desktopRules = styles.slice(styles.lastIndexOf("@media (min-width: 801px)"));
  assert.match(desktopRules, /width \.3\d*s cubic-bezier\(\.16,\s*1,\s*\.3,\s*1\)/);
  assert.match(desktopRules, /margin-left \.3\d*s cubic-bezier\(\.16,\s*1,\s*\.3,\s*1\)/);
});

test("sidebar labels fade and slide before becoming hidden", () => {
  const desktopRules = styles.slice(styles.lastIndexOf("@media (min-width: 801px)"));
  assert.match(desktopRules, /\.app-shell\.sidebar-collapsed \.sidebar \.navigation-item > span[\s\S]*?opacity: 0;[\s\S]*?visibility: hidden;/);
  assert.doesNotMatch(desktopRules, /\.app-shell\.sidebar-collapsed \.sidebar \.navigation-item > span \{ display: none; \}/);
});

test("sidebar animation honors reduced-motion preferences", () => {
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.sidebar[\s\S]*?transition-duration: \.01ms/);
});
