import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "playwright";

const themes = [
  ["Default", "default"], ["Light", "light"], ["Dark", "dark"],
  ["Skeuomorphism", "skeuomorphism"], ["Neumorphism", "neumorphism"],
  ["Brutalism", "brutalism"], ["Retro Terminal", "retro-terminal"],
  ["Elegant Plain", "elegant-plain"], ["Bento Grid", "bento-grid"],
  ["Nordic", "nordic"], ["Editorial", "editorial"],
];
const server = spawn("npm", ["run", "dev", "--", "--host", "127.0.0.1"], {
  stdio: ["ignore", "pipe", "pipe"],
});
let serverOutput = "";
server.stdout.on("data", (chunk) => { serverOutput += chunk.toString(); });
server.stderr.on("data", (chunk) => { serverOutput += chunk.toString(); });

let browser;
try {
  let ready = false;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch("http://127.0.0.1:5173/");
      if (response.ok) { ready = true; break; }
    } catch { /* Vite is still starting. */ }
    await delay(1000);
  }
  assert.ok(ready, `Vite did not become ready. Output:\n${serverOutput}`);

  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  const response = await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle" });
  assert.equal(response?.status(), 200, "Landing page must return HTTP 200");
  assert.ok(await page.locator("body").innerText().then((text) => text.trim().length > 0), "Landing page must render visible content");

  // Exercise the same shared selectors used by Accounts-style tabs, Tax navigation,
  // Market research tabs, form controls, and cards, without touching user data or APIs.
  await page.evaluate(() => {
    const fixture = document.createElement("div");
    fixture.id = "theme-browser-audit-fixture";
    fixture.innerHTML = `
      <main class="content">
        <div class="tab fixture-tab">Inactive tab</div>
        <div class="tab active fixture-tab-active">Active tab</div>
        <input aria-label="Theme audit input" value="Readable input" />
        <div class="card fixture-card">Card surface</div>
        <button class="primary-button fixture-primary">Primary action</button>
        <button class="secondary-button fixture-secondary">Secondary action</button>
        <button class="fixture-disabled" disabled>Disabled action</button>
      </main>
      <section class="tax-centre">
        <nav aria-label="Tax sections"><button>Inactive tax tab</button><button class="active">Active tax tab</button></nav>
        <div class="tax-section-card">Tax panel</div>
      </section>
      <section class="markets-workspace">
        <div class="market-card">Market panel</div>
        <input aria-label="Market audit input" value="NSE" />
        <div class="instrument-research-panel"><button class="instrument-research-tab">Overview</button><button class="instrument-research-tab is-active">Fundamentals</button></div>
      </section>`;
    fixture.style.cssText = "position:fixed;left:-10000px;top:0;width:600px;z-index:-1";
    document.body.appendChild(fixture);
  });

  const results = [];
  for (const [label, slug] of themes) {
    const result = await page.evaluate((themeSlug) => {
      document.documentElement.dataset.finosTheme = themeSlug;
      const root = getComputedStyle(document.documentElement);
      const get = (selector) => {
        const node = document.querySelector(selector);
        if (!node) throw new Error(`Missing browser fixture selector: ${selector}`);
        return getComputedStyle(node);
      };
      const inactive = get("#theme-browser-audit-fixture .fixture-tab");
      const active = get("#theme-browser-audit-fixture .fixture-tab-active");
      const input = get("#theme-browser-audit-fixture input");
      const card = get("#theme-browser-audit-fixture .fixture-card");
      const primary = get("#theme-browser-audit-fixture .fixture-primary");
      const disabled = get("#theme-browser-audit-fixture .fixture-disabled");
      const taxTab = get("#theme-browser-audit-fixture .tax-centre nav button.active");
      const marketCard = get("#theme-browser-audit-fixture .markets-workspace .market-card");
      const researchTab = get("#theme-browser-audit-fixture .instrument-research-tab.is-active");
      return {
        page: root.getPropertyValue("--th-page").trim(),
        text: root.getPropertyValue("--th-text").trim(),
        cardToken: root.getPropertyValue("--th-card").trim(),
        accent: root.getPropertyValue("--th-accent").trim(),
        inactiveBackground: inactive.backgroundColor,
        inactiveImage: inactive.backgroundImage,
        activeBackground: active.backgroundColor,
        activeImage: active.backgroundImage,
        inactiveBorder: inactive.borderColor,
        activeBorder: active.borderColor,
        inactiveShadow: inactive.boxShadow,
        activeShadow: active.boxShadow,
        inputBackground: input.backgroundColor,
        inputColor: input.color,
        cardBackground: card.backgroundColor,
        primaryBackground: primary.backgroundColor,
        primaryColor: primary.color,
        disabledOpacity: disabled.opacity,
        taxBackground: taxTab.backgroundColor,
        marketBackground: marketCard.backgroundColor,
        researchBackground: researchTab.backgroundColor,
        tabRadius: active.borderRadius,
        pageBackground: getComputedStyle(document.body).backgroundColor,
      };
    }, slug);

    assert.ok(result.page && result.text && result.cardToken && result.accent, `${label}: required theme tokens must resolve`);
    assert.ok(result.inputBackground !== "rgba(0, 0, 0, 0)" || result.inputColor !== "rgba(0, 0, 0, 0)", `${label}: input must have theme styling`);
    assert.ok(result.cardBackground !== "rgba(0, 0, 0, 0)", `${label}: card surface must be styled`);
    assert.ok(result.primaryBackground !== "rgba(0, 0, 0, 0)", `${label}: primary button must have a visible surface`);
    assert.ok(result.primaryColor !== "rgba(0, 0, 0, 0)", `${label}: primary button text must be visible`);
    assert.equal(result.disabledOpacity, "0.55", `${label}: disabled state must be visually indicated`);
    assert.ok(result.tabRadius.length > 0, `${label}: tab geometry token must resolve`);
    const inactiveStyle = [result.inactiveBackground, result.inactiveImage, result.inactiveBorder, result.inactiveShadow].join("|");
    const activeStyle = [result.activeBackground, result.activeImage, result.activeBorder, result.activeShadow].join("|");
    assert.notEqual(activeStyle, inactiveStyle, `${label}: selected and unselected tabs must be distinguishable`);
    assert.ok(result.taxBackground.length > 0 && result.marketBackground.length > 0 && result.researchBackground.length > 0,
      `${label}: Tax and Market controls/panels must resolve styles`);
    results.push(label);
  }

  // Test a narrow viewport for horizontal overflow on the real landing page.
  await page.evaluate(() => document.querySelector("#theme-browser-audit-fixture")?.remove());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle" });
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    page: document.documentElement.scrollWidth,
  }));
  assert.ok(dimensions.page <= dimensions.viewport + 2,
    `Landing page overflows at 390px: viewport=${dimensions.viewport}, page=${dimensions.page}`);
  assert.deepEqual(pageErrors, [], `Browser runtime errors: ${pageErrors.join("; ")}`);

  console.log(`PASS: Chromium rendered the landing page and verified shared component styles for ${results.length} themes: ${results.join(", ")}.`);
  console.log("PASS: selected/unselected tabs, inputs, cards, primary/disabled buttons, Tax/Market selectors, and 390px landing-page overflow check.");
  console.log("LIMIT: authenticated data screens are not covered because this test intentionally uses no account credentials or live API data.");
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
