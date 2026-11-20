import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const app = read("../../App.jsx");
const chartPage = read("../advanced-chart/AdvancedChartPage.jsx");
const chartCss = read("../advanced-chart/advanced-chart.css");
const corporatePanel = read("./CorporateActionsPanel.jsx");

test("Market instrument research owns the Corporate Actions tab and panel", () => {
  assert.match(app, /import CorporateActionsPanel from ".\/features\/market-intelligence\/CorporateActionsPanel\.jsx"/);
  assert.match(app, /tabButton\("dividends", "Corporate Actions"\)/);
  assert.match(app, /researchTab === "dividends"[\s\S]*?<CorporateActionsPanel instrument=\{selectedInstrument\} \/>/);
});

test("Advanced Chart remains independent of Corporate Actions", () => {
  assert.doesNotMatch(chartPage, /CorporateActionsPanel|loadCorporateActions|corporate-actions/);
  for (const preserved of ["createChart", "loadChartHistory", "loadLatestQuote", "MarketMoversScanner", "chartContainerRef", "advanced-chart-canvas", "advanced-chart-indicator-pane"]) {
    assert.ok(chartPage.includes(preserved), `Advanced Chart regression: missing ${preserved}`);
  }
  assert.doesNotMatch(chartCss, /advanced-chart-corporate/);
  assert.match(chartCss, /\.advanced-chart-canvas/);
  assert.match(chartCss, /\.advanced-chart-indicator-pane/);
});

test("Corporate Actions panel loads only the selected instrument and presents source context", () => {
  assert.match(corporatePanel, /loadCorporateActions\(instrument\)/);
  assert.match(corporatePanel, /dividend_per_share/);
  assert.match(corporatePanel, /ex_date/);
  assert.match(corporatePanel, /record_date/);
  assert.match(corporatePanel, /book_closure/);
  assert.match(corporatePanel, /source/);
});
