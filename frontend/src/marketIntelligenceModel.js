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
      change: finiteOrNull(row.change_pct ?? row.percent_change ?? row.change_percent ?? row.change),
      exchange: row.exchange || null,
      status: row.status || null,
    };
  }) : [];
  const movers = payload.market_movers && typeof payload.market_movers === 'object' ? payload.market_movers : {};
  const cleanMovers = (rows) => Array.isArray(rows) ? rows.filter((row) => row && typeof row === 'object' && !Array.isArray(row)).map((row) => ({
    symbol: row.symbol || row.trading_symbol || row.name || 'Unknown instrument',
    instrumentKey: `${String(row.exchange || 'UNKNOWN').trim().toUpperCase()}:${String(row.symbol || row.trading_symbol || row.name || 'UNKNOWN').trim().toUpperCase()}`,
    name: row.name || row.symbol || row.trading_symbol || 'Unknown instrument',
    change: finiteOrNull(row.change_pct ?? row.percent_change ?? row.change_percent ?? row.change),
    price: finiteOrNull(row.last_price ?? row.ltp),
    exchange: row.exchange || null,
  })) : [];
  return { indices, gainers: cleanMovers(movers.gainers), losers: cleanMovers(movers.losers) };
}


export function getFlowRows(snapshot) {
  const source = snapshot && typeof snapshot === 'object' ? snapshot : {};
  const rows = [
    ...(Array.isArray(source.gainers) ? source.gainers : []),
    ...(Array.isArray(source.losers) ? source.losers : []),
  ];
  const seen = new Set();
  return rows
    .filter((row) => row && typeof row === 'object')
    .map((row) => ({
      ...row,
      symbol: String(row.symbol || row.name || 'Unknown').trim().toUpperCase(),
      instrumentKey: String(row.instrumentKey || `${String(row.exchange || 'UNKNOWN').trim().toUpperCase()}:${String(row.symbol || row.name || 'Unknown').trim().toUpperCase()}`),
      change: finiteOrNull(row.change),
      price: finiteOrNull(row.price),
    }))
    .filter((row) => {
      if (seen.has(row.instrumentKey)) return false;
      seen.add(row.instrumentKey);
      return true;
    })
    .sort((a, b) => {
      const av = a.change;
      const bv = b.change;
      if (av === null && bv === null) return a.symbol.localeCompare(b.symbol);
      if (av === null) return 1;
      if (bv === null) return -1;
      return bv - av;
    });
}

export function filterFlowRows(rows, { query = '', direction = 'all', sort = 'change' } = {}) {
  const needle = String(query).trim().toUpperCase();
  const filtered = (Array.isArray(rows) ? rows : []).filter((row) => {
    const matchesQuery = !needle || row.symbol.includes(needle) || String(row.name || '').toUpperCase().includes(needle);
    const matchesDirection = direction === 'all' || (direction === 'up' && row.change > 0) || (direction === 'down' && row.change < 0) || (direction === 'flat' && row.change === 0) || (direction === 'unknown' && row.change === null);
    return matchesQuery && matchesDirection;
  });
  return [...filtered].sort((a, b) => {
    if (sort === 'symbol') return a.symbol.localeCompare(b.symbol);
    if (sort === 'price') return (b.price ?? -Infinity) - (a.price ?? -Infinity);
    return (b.change ?? -Infinity) - (a.change ?? -Infinity);
  });
}


export function getMarketFeedState({ status, hasData, lastSuccessAt, now = Date.now(), staleAfterMs = 30000 } = {}) {
  if (!hasData || !Number.isFinite(lastSuccessAt)) {
    return { label: 'Disconnected', kind: 'disconnected', stale: false };
  }
  const stale = now - lastSuccessAt > staleAfterMs;
  if (stale || status === 'error') return { label: 'Stale snapshot', kind: 'stale', stale: true };
  if (status === 'partial') return { label: 'Partial snapshot', kind: 'partial', stale: false };
  return { label: 'Snapshot received', kind: 'snapshot', stale: false };
}
