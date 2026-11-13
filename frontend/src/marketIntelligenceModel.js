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


export function mergeStreamTicks(rows, ticks) {
  const byInstrument = new Map();
  (Array.isArray(ticks) ? ticks : []).forEach((tick) => {
    const key = tick?.instrument?.instrument_key;
    if (key && Number.isFinite(Number(tick.ltp)) && Number(tick.ltp) > 0) byInstrument.set(key, tick);
  });
  return (Array.isArray(rows) ? rows : []).map((row) => {
    const tick = byInstrument.get(row.instrumentKey);
    if (!tick) return { ...row, feedSource: row.feedSource || 'Overview snapshot' };
    const close = finiteOrNull(tick.close);
    const livePrice = finiteOrNull(tick.ltp);
    const liveChange = close !== null && close > 0 && livePrice !== null
      ? ((livePrice - close) / close) * 100
      : row.change;
    return {
      ...row,
      price: livePrice,
      change: liveChange,
      feedSource: 'm.Stock WebSocket',
      tickAt: tick.exchange_time || null,
      openInterest: finiteOrNull(tick.open_interest),
      volume: finiteOrNull(tick.volume),
      marketDepth: Array.isArray(tick.bids) && Array.isArray(tick.asks)
        ? { bids: tick.bids, asks: tick.asks }
        : null,
    };
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


export function getHistoricalChartRows(payload) {
  const source = Array.isArray(payload?.data) ? payload.data : Array.isArray(payload?.candles) ? payload.candles : [];
  return source.flatMap((candle) => {
    const row = Array.isArray(candle) ? {
      timestamp: candle[0], open: candle[1], high: candle[2], low: candle[3], close: candle[4], volume: candle[5],
    } : candle;
    if (!row || typeof row !== 'object' || !row.timestamp) return [];
    const open = finiteOrNull(row.open);
    const high = finiteOrNull(row.high);
    const low = finiteOrNull(row.low);
    const close = finiteOrNull(row.close);
    const volume = finiteOrNull(row.volume);
    if ([open, high, low, close, volume].some((value) => value === null) || Math.min(open, high, low, close) <= 0 || volume < 0 || high < Math.max(open, low, close) || low > Math.min(open, high, close)) return [];
    return [{ timestamp: String(row.timestamp), open, high, low, close, volume }];
  });
}


export function getOptionMasterChoices(payload) {
  const data = payload && typeof payload === 'object' ? payload : {};
  const expiries = data.expiries && typeof data.expiries === 'object' ? data.expiries : {};
  const expiryChoices = Object.entries(expiries).flatMap(([id, timestamp]) => {
    const value = finiteOrNull(timestamp);
    return value !== null && value > 0 ? [{ id, timestamp: value }] : [];
  }).sort((a, b) => a.timestamp - b.timestamp);
  const groups = data.underlyings && typeof data.underlyings === 'object' ? data.underlyings : {};
  const underlyings = ['OPTIDX', 'OFSTK'].flatMap((group) => Array.isArray(groups[group]) ? groups[group] : []).flatMap((raw) => {
    if (typeof raw !== 'string') return [];
    const [symbol, token, ...expiryIds] = raw.split(',').map((part) => part.trim());
    if (!symbol || !/^\d+$/.test(token || '')) return [];
    const validExpiryIds = expiryIds.filter((id) => expiryChoices.some((expiry) => expiry.id === id));
    return validExpiryIds.length ? [{ symbol, token: Number(token), expiryIds: validExpiryIds }] : [];
  });
  return { expiryChoices, underlyings };
}

export function getOptionRows(payload) {
  const source = Array.isArray(payload?.options) ? payload.options : [];
  return source.flatMap((row) => {
    if (!row || typeof row !== 'object') return [];
    const strike = finiteOrNull(row.strike);
    const callOI = finiteOrNull(row.call_oi);
    const putOI = finiteOrNull(row.put_oi);
    if (strike === null || strike <= 0 || callOI === null || callOI < 0 || putOI === null || putOI < 0) return [];
    return [{ strike, call_oi: callOI, put_oi: putOI }];
  }).sort((a, b) => a.strike - b.strike);
}
