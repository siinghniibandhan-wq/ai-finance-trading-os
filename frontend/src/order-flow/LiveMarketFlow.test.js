import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { build } from "esbuild";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { unlink } from "node:fs/promises";

test("LiveMarketFlow renders provider contracts and explicit unavailable fields", async () => {
  const directory = dirname(fileURLToPath(import.meta.url));
  const output = join(directory, `.LiveMarketFlow.component-test-${process.pid}.mjs`);
  try {
    await build({
      entryPoints: [join(directory, "LiveMarketFlow.jsx")],
      outfile: output,
      bundle: true,
      platform: "node",
      format: "esm",
      packages: "external",
      jsx: "automatic",
    });
    const { default: LiveMarketFlow } = await import(pathToFileURL(output).href + `?run=${Date.now()}`);
    const markup = renderToStaticMarkup(React.createElement(LiveMarketFlow, {
      symbol: "NIFTY",
      onSymbolChange: () => {},
      snapshot: {
        futures_contracts: [{
          symbol: "NIFTY", tradingsymbol: "NIFTY26NOVFUT",
          expiry: "2026-11-26", price: 25000, oi: 1200, volume: 10,
        }],
        option_oi_by_strike: [
          { strike: 24900, ce_oi: 100, pe_oi: 300 },
          { strike: 25000, ce_oi: 500, pe_oi: 200 },
        ],
        coverage: {
          unavailable: [{ tradingsymbol: "NIFTY26DECFUT", reason: "no tick received" }],
        },
        feed: { last_tick_at: "2026-11-17T09:20:00+00:00" },
        historical_oi_included: false,
      },
    }));

    assert.match(markup, /NIFTY derivatives/);
    assert.match(markup, /NIFTY26NOVFUT/);
    assert.match(markup, /25,000/);
    assert.match(markup, /NIFTY26DECFUT/);
    assert.match(markup, /unavailable: no tick received/);
    assert.match(markup, /Intraday candles/);
    assert.match(markup, /Buildup/);
    assert.match(markup, /OI change %/);
    assert.match(markup, /Unavailable/);
    assert.doesNotMatch(markup, /DEMO|SIMULATED/);
  } finally {
    await unlink(output).catch(() => {});
  }
});
