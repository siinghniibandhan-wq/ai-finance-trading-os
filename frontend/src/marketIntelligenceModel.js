export function getMetricDisplay(value) {
  if (value === null || value === undefined || value === '') return 'Not connected';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'Not connected';
  if (typeof value === 'string') return value;
  return 'Not connected';
}

export function getCompletionSummary(items) {
  const rows = Array.isArray(items) ? items : [];
  return {
    built: rows.filter((item) => item.implementation === 'built').length,
    integrated: rows.filter((item) => item.integration === 'integrated').length,
    total: rows.length,
  };
}

const finiteOrNull = (value) => value === null || value === undefined || value === '' ? null : (Number.isFinite(Number(value)) ? Number(value) : null);

export function getMarketSnapshot(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return { indices: [], gainers: [], losers: [] };
  }
  const indices = Array.isArray(payload.indices) ? payload.indices.filter((row) => row && typeof row === 'object' && !Array.isArray(row)).map((row) => {
    const raw = row.last_price ?? row.ltp ?? row.value;
    return {
      label: row.name || row.symbol || row.index || 'Market index',
      value: finiteOrNull(raw),
      change: finiteOrNull(row.change_pct),
      exchange: row.exchange || null,
      status: row.status || null,
    };
  }) : [];
  const movers = payload.market_movers && typeof payload.market_movers === 'object' ? payload.market_movers : {};
  const cleanMovers = (rows) => Array.isArray(rows) ? rows.filter((row) => row && typeof row === 'object' && !Array.isArray(row)).map((row) => ({
    symbol: row.symbol || row.trading_symbol || row.name || 'Unknown instrument',
    name: row.name || row.symbol || row.trading_symbol || 'Unknown instrument',
    change: finiteOrNull(row.change_pct ?? row.percent_change ?? row.change_percent),
    price: finiteOrNull(row.last_price ?? row.ltp),
    exchange: row.exchange || null,
  })) : [];
  return { indices, gainers: cleanMovers(movers.gainers), losers: cleanMovers(movers.losers) };
}
