const finite = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

/**
 * Normalize only provider-returned m.Stock market-mover rows.
 * Missing identifiers, exchanges, prices or percentage changes are rejected.
 */
export function normalizeMoverRows(rawRows) {
  if (!Array.isArray(rawRows)) return [];
  const rows = [];
  for (const row of rawRows) {
    const symbol = String(row?.symbol || "").trim().toUpperCase();
    const exchange = String(row?.exchange || "").trim().toUpperCase();
    const lastPrice = finite(row?.ltp);
    const changePercent = finite(row?.percent_change);
    if (!symbol || !["NSE", "BSE"].includes(exchange) ||
        lastPrice === null || lastPrice <= 0 || changePercent === null) continue;
    rows.push({
      symbol,
      exchange,
      name: String(row?.name || symbol),
      lastPrice,
      changePercent,
      volume: finite(row?.volume),
    });
  }
  return rows.sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent));
}

export function summarizeMoverRows(rows) {
  const valid = Array.isArray(rows) ? rows : [];
  const withVolume = valid.filter((row) => Number.isFinite(row.volume));
  return {
    count: valid.length,
    averageChangePercent: valid.length
      ? valid.reduce((sum, row) => sum + row.changePercent, 0) / valid.length
      : null,
    totalReportedVolume: withVolume.length
      ? withVolume.reduce((sum, row) => sum + row.volume, 0)
      : null,
    rowsWithVolume: withVolume.length,
  };
}
