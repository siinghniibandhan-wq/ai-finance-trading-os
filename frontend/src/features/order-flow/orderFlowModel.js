const num=v=>{if(v===null||v===undefined||v==="")return null;const n=Number(v);return Number.isFinite(n)?n:null;};
export function normalizeOrderFlow(payload){const out=[];const source=payload?.market_movers||{};for(const key of ["gainers","losers"]){for(const row of Array.isArray(source[key])?source[key]:[]){const symbol=String(row?.symbol||"").trim().toUpperCase(),exchange=String(row?.exchange||"").trim().toUpperCase(),price=num(row?.ltp),changePercent=num(row?.percent_change);if(!symbol||!["NSE","BSE"].includes(exchange)||price===null||price<=0||changePercent===null)continue;out.push({symbol,exchange,name:String(row?.name||symbol),price,changePercent,volume:num(row?.volume),sector:typeof row?.sector==="string"&&row.sector.trim()?row.sector.trim():null,direction:changePercent>0?"bullish":changePercent<0?"bearish":"unchanged"});}}const unique=new Map();out.forEach(r=>unique.set(r.exchange+":"+r.symbol,r));return [...unique.values()];}
export function summarizeOrderFlow(rows){const safe=Array.isArray(rows)?rows:[],bullish=safe.filter(r=>r.direction==="bullish").length,bearish=safe.filter(r=>r.direction==="bearish").length,unchanged=safe.filter(r=>r.direction==="unchanged").length,total=safe.length;return{bullish,bearish,unchanged,total,bullishShare:total?bullish/total:null,bearishShare:total?bearish/total:null};}
export function sortOrderFlow(rows,key="changePercent",direction="desc"){const sign=direction==="asc"?1:-1;return[...(rows||[])].sort((a,b)=>{if(key==="symbol")return String(a.symbol||"").localeCompare(String(b.symbol||""))*sign;const x=num(a[key]),y=num(b[key]);if(x===null&&y===null)return String(a.symbol||"").localeCompare(String(b.symbol||""));if(x===null)return 1;if(y===null)return-1;return(x-y)*sign;});}
export function buildChartFlowPoints(rows,limit=36){const safe=(Array.isArray(rows)?rows:[]).filter(r=>Number.isFinite(num(r.changePercent)));const ranked=[...safe].sort((a,b)=>Math.abs(b.changePercent)-Math.abs(a.changePercent)||a.symbol.localeCompare(b.symbol)).slice(0,Math.max(0,limit));const maxAbs=Math.max(0.1,...ranked.map(r=>Math.abs(r.changePercent)));return ranked.map((r,index)=>({...r,normalizedMove:r.changePercent/maxAbs,rank:index}));}


/** Organise the latest validated provider snapshot; this is not a full-exchange breadth estimate. */
export function buildMarketFlowBoard(rows, perSide = 12, sortKey = "changePercent", sortDirection = "desc") {
  const safe = Array.isArray(rows) ? rows.filter(row => Number.isFinite(Number(row.changePercent))) : [];
  const bullish = sortOrderFlow(safe.filter(row => row.changePercent > 0), sortKey, sortDirection);
  const bearishDirection = sortKey === "changePercent" ? (sortDirection === "asc" ? "desc" : "asc") : sortDirection;
  const bearish = sortOrderFlow(safe.filter(row => row.changePercent < 0), sortKey, bearishDirection);
  const unchanged = sortOrderFlow(safe.filter(row => row.changePercent === 0), "symbol", "asc");
  return {
    bullish, bearish, unchanged,
    visibleBullish: bullish.slice(0, Math.max(0, perSide)),
    visibleBearish: bearish.slice(0, Math.max(0, perSide)),
    distribution: [...safe].sort((a, b) => a.changePercent - b.changePercent),
    maxAbs: Math.max(0.1, ...safe.map(row => Math.abs(row.changePercent))),
    counts: { bullish: bullish.length, bearish: bearish.length, unchanged: unchanged.length, total: safe.length },
  };
}

/** Position each dot using only an actual provider-reported percentage change. */
export function buildDistributionDots(rows, width = 1000, height = 74) {
  const safe = Array.isArray(rows) ? rows.filter(row => Number.isFinite(Number(row.changePercent))) : [];
  if (!safe.length) return [];
  const maxAbs = Math.max(0.1, ...safe.map(row => Math.abs(row.changePercent)));
  const center = width / 2;
  const half = width * 0.46;
  const buckets = new Map();
  return [...safe].sort((a, b) => a.changePercent - b.changePercent).map(row => {
    const x = center + row.changePercent / maxAbs * half;
    const bucket = Math.round(x / 7);
    const stack = buckets.get(bucket) || 0;
    buckets.set(bucket, stack + 1);
    return { ...row, x, y: height / 2 + (stack % 2 ? 1 : -1) * Math.ceil(stack / 2) * 5 };
  });
}


/** Normalize the selected sector's actual provider-ranked gainers and losers. */
export function normalizeSectorMovers(payload) {
  const rows = normalizeOrderFlow({ market_movers: payload?.movers });
  const sector = String(payload?.sector?.name || "").trim() || null;
  return rows.map(row => ({ ...row, sector }));
}


/** Filter only rows present in the validated provider snapshot. */
export function filterOrderFlow(rows, filters = {}) {
  const query = String(filters.query || "").trim().toLowerCase();
  const exchange = String(filters.exchange || "ALL").trim().toUpperCase();
  const direction = String(filters.direction || "ALL").trim().toLowerCase();
  return (Array.isArray(rows) ? rows : []).filter(row => {
    if (exchange !== "ALL" && row.exchange !== exchange) return false;
    if (direction !== "all" && row.direction !== direction) return false;
    if (!query) return true;
    return [row.symbol, row.name, row.exchange, row.sector]
      .some(value => String(value || "").toLowerCase().includes(query));
  });
}


/** Build a relative-price and volume series from existing market-chart OHLCV rows. */
export function buildHistoricalFlowSeries(candles) {
  const valid = (Array.isArray(candles) ? candles : []).map(row => {
    const open = num(row?.open);
    const high = num(row?.high);
    const low = num(row?.low);
    const close = num(row?.close);
    const volume = num(row?.volume);
    const timestamp = row?.timestamp;
    if (
      timestamp === null || timestamp === undefined ||
      [open, high, low, close].some(value => value === null || value <= 0) ||
      high < Math.max(open, close, low) ||
      low > Math.min(open, close, high)
    ) return null;
    return { timestamp, open, high, low, close, volume: volume !== null && volume >= 0 ? volume : null };
  }).filter(Boolean);
  const base = valid[0]?.close;
  if (!base || base <= 0) return [];
  return valid.map(row => ({
    ...row,
    relativeChange: ((row.close - base) / base) * 100,
  }));
}


/** Summary of the provider-ranked rows returned for a selected sector, not the whole sector universe. */
export function summarizeSectorMoverSample(rows) {
  const changes = (Array.isArray(rows) ? rows : [])
    .map(row => num(row?.changePercent))
    .filter(value => value !== null)
    .sort((a, b) => a - b);
  const count = changes.length;
  const middle = Math.floor(count / 2);
  const medianChangePct = count === 0
    ? null
    : count % 2
      ? changes[middle]
      : (changes[middle - 1] + changes[middle]) / 2;
  return {
    count,
    medianChangePct,
    bullish: changes.filter(value => value > 0).length,
    bearish: changes.filter(value => value < 0).length,
    unchanged: changes.filter(value => value === 0).length,
  };
}


/** Rank sector labels by the percentage change calculated from provider LTP and previous-close OHLC. */
export function rankSectorIndices(sectors, quotes) {
  const byKey = new Map((Array.isArray(quotes) ? quotes : []).map(item => [item.key, item]));
  return [...(Array.isArray(sectors) ? sectors : [])].sort((a, b) => {
    const av = byKey.get(a.key)?.percent_change;
    const bv = byKey.get(b.key)?.percent_change;
    const aValue = av === null || av === undefined || !Number.isFinite(Number(av)) ? null : Number(av);
    const bValue = bv === null || bv === undefined || !Number.isFinite(Number(bv)) ? null : Number(bv);
    if (aValue === null && bValue === null) return 0;
    if (aValue === null) return 1;
    if (bValue === null) return -1;
    return bValue - aValue;
  });
}


/** Sum only provider-reported volume for the current returned mover set. */
export function summarizeMoverVolume(rows) {
  const summary = {
    bullishVolume: 0, bearishVolume: 0, unchangedVolume: 0,
    bullishCount: 0, bearishCount: 0, unchangedCount: 0, volumeReported: 0,
  };
  for (const row of Array.isArray(rows) ? rows : []) {
    const volume = num(row?.volume);
    if (volume === null || volume < 0) continue;
    if (row.direction === "bullish") {
      summary.bullishVolume += volume;
      summary.bullishCount += 1;
    } else if (row.direction === "bearish") {
      summary.bearishVolume += volume;
      summary.bearishCount += 1;
    } else if (row.direction === "unchanged") {
      summary.unchangedVolume += volume;
      summary.unchangedCount += 1;
    } else continue;
    summary.volumeReported += 1;
  }
  return summary;
}


/**
 * Build the sector-flow rail from the provider's sector universe and index
 * quotes. Missing quotes and missing percentage changes remain unavailable;
 * index levels are never treated as performance.
 */
export function buildSectorFlowRows(sectors, quotes) {
  const byKey = new Map((Array.isArray(quotes) ? quotes : []).map(item => [item.key, item]));
  return (Array.isArray(sectors) ? sectors : [])
    .map(sector => {
      const quote = byKey.get(sector.key);
      const rawChange = num(quote?.percent_change);
      const percentChange = rawChange === null ? null : rawChange;
      const lastPrice = num(quote?.last_price);
      return {
        key: sector.key,
        name: sector.name,
        indexSymbol: sector.index_symbol || quote?.index_symbol || null,
        lastPrice: lastPrice !== null && lastPrice > 0 ? lastPrice : null,
        percentChange,
        direction: percentChange === null ? null
          : percentChange > 0 ? "bullish"
            : percentChange < 0 ? "bearish" : "unchanged",
      };
    })
    .sort((a, b) => {
      if (a.percentChange === null && b.percentChange === null) return a.name.localeCompare(b.name);
      if (a.percentChange === null) return 1;
      if (b.percentChange === null) return -1;
      return b.percentChange - a.percentChange;
    });
}


/** Map validated daily OHLCV observations to deterministic SVG candlestick geometry. */
export function buildHistoricalCandleGeometry(series, width = 720, height = 196) {
  const valid = (Array.isArray(series) ? series : []).filter(row => {
    const values = [row?.open, row?.high, row?.low, row?.close];
    if (!values.every(value =>
      value !== null && value !== undefined && Number.isFinite(Number(value)) && Number(value) > 0
    )) return false;
    const [open, high, low, close] = values.map(Number);
    return high >= Math.max(open, close, low) && low <= Math.min(open, close, high);
  });
  if (!valid.length) return [];
  const min = Math.min(...valid.map(row => Number(row.low)));
  const max = Math.max(...valid.map(row => Number(row.high)));
  const span = Math.max(max - min, max * 0.001, 0.01);
  const plotTop = 18;
  const plotHeight = 112;
  const volumeBase = 184;
  const maxVolume = Math.max(1, ...valid.map(row => {
    const value = num(row.volume);
    return value !== null && value >= 0 ? value : 0;
  }));
  const xPadding = 24;
  const candleSlot = valid.length > 1
    ? (width - xPadding * 2) / (valid.length - 1)
    : width - xPadding * 2;
  const bodyWidth = Math.max(0.35, Math.min(7, candleSlot * 0.65));
  return valid.map((row, index) => {
    const x = xPadding + (valid.length === 1 ? 0 : index / (valid.length - 1) * (width - xPadding * 2));
    const y = value => plotTop + ((max - Number(value)) / span) * plotHeight;
    const openY = y(row.open);
    const closeY = y(row.close);
    const volume = num(row.volume);
    const volumeHeight = volume === null || volume < 0 ? 0 : volume / maxVolume * 36;
    return {
      timestamp: row.timestamp,
      x,
      highY: y(row.high),
      lowY: y(row.low),
      openY,
      closeY,
      bodyTop: Math.min(openY, closeY),
      bodyHeight: Math.max(1, Math.abs(openY - closeY)),
      bodyWidth,
      volumeY: volumeBase - volumeHeight,
      volumeHeight,
      direction: Number(row.close) >= Number(row.open) ? "bullish" : "bearish",
      open: Number(row.open),
      high: Number(row.high),
      low: Number(row.low),
      close: Number(row.close),
      volume,
    };
  });
}
