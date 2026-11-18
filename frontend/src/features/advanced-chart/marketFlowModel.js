const finite = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

/**
 * Convert only provider-supplied market movers into directional flow rows.
 * Direction is based on the provider's percent_change; no flow volume or
 * capital movement is inferred from price change.
 */
export function normalizeMarketFlow(payload) {
  const raw = payload?.market_movers || {};
  const groups = { bullish: [], bearish: [], unchanged: [] };

  for (const [key, target] of [["gainers", "bullish"], ["losers", "bearish"]]) {
    const rows = Array.isArray(raw[key]) ? raw[key] : [];
    for (const row of rows) {
      const symbol = String(row?.symbol || "").trim().toUpperCase();
      const exchange = String(row?.exchange || "").trim().toUpperCase();
      const lastPrice = finite(row?.ltp);
      const changePercent = finite(row?.percent_change);
      if (!symbol || !["NSE", "BSE"].includes(exchange) || lastPrice === null ||
          lastPrice <= 0 || changePercent === null) continue;
      const direction = changePercent > 0 ? "bullish" : changePercent < 0 ? "bearish" : "unchanged";
      groups[direction].push({
        symbol,
        exchange,
        name: String(row?.name || symbol),
        lastPrice,
        changePercent,
        volume: finite(row?.volume),
      });
    }
  }

  const sortByMagnitude = (a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent);
  groups.bullish.sort(sortByMagnitude);
  groups.bearish.sort(sortByMagnitude);
  return groups;
}

export function summarizeMarketFlow(groups) {
  const bullish = Array.isArray(groups?.bullish) ? groups.bullish.length : 0;
  const bearish = Array.isArray(groups?.bearish) ? groups.bearish.length : 0;
  const unchanged = Array.isArray(groups?.unchanged) ? groups.unchanged.length : 0;
  return {
    bullish,
    bearish,
    unchanged,
    advancingShare: bullish + bearish + unchanged
      ? bullish / (bullish + bearish + unchanged)
      : null,
  };
}


/** Build connector geometry from provider-reported percentage changes, never generated prices or time-series points. */
export function buildMarketFlowDiagram(groups, { width = 1200, height = 700 } = {}) {
  const zeroY = height / 2;
  const scale = Math.max(8, height * 0.055);
  const connections = [];
  for (const side of ["bullish", "bearish"]) {
    const rows = Array.isArray(groups?.[side]) ? groups[side] : [];
    rows.forEach((item, index) => {
      const change = finite(item.changePercent);
      if (!item.symbol || change === null || change === 0 || !Number.isFinite(item.lastPrice) || item.lastPrice <= 0) return;
      const magnitude = Math.min(Math.abs(change), 10);
      const endY = Math.max(18, Math.min(height - 18, zeroY + (side === "bullish" ? -1 : 1) * magnitude * scale));
      const tileY = side === "bullish"
        ? Math.min(zeroY - 18, 42 + index * 32)
        : Math.max(zeroY + 18, height - 42 - index * 32);
      const path = `M 180 ${zeroY} C 340 ${zeroY}, 390 ${endY}, 560 ${endY} S 690 ${tileY}, 760 ${tileY}`;
      connections.push({ symbol: item.symbol, exchange: item.exchange, side, changePercent: change, endY, tileY, path });
    });
  }
  return { width, height, zeroY, connections };
}
