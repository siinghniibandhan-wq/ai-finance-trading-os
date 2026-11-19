const num=v=>{if(v===null||v===undefined||v==="")return null;const n=Number(v);return Number.isFinite(n)?n:null;};
export function normalizeOrderFlow(payload){const out=[];const source=payload?.market_movers||{};for(const key of ["gainers","losers"]){for(const row of Array.isArray(source[key])?source[key]:[]){const symbol=String(row?.symbol||"").trim().toUpperCase(),exchange=String(row?.exchange||"").trim().toUpperCase(),price=num(row?.ltp),changePercent=num(row?.percent_change);if(!symbol||!["NSE","BSE"].includes(exchange)||price===null||price<=0||changePercent===null)continue;out.push({symbol,exchange,name:String(row?.name||symbol),price,changePercent,volume:num(row?.volume),sector:typeof row?.sector==="string"&&row.sector.trim()?row.sector.trim():null,direction:changePercent>0?"bullish":changePercent<0?"bearish":"unchanged"});}}const unique=new Map();out.forEach(r=>unique.set(r.exchange+":"+r.symbol,r));return [...unique.values()];}
export function summarizeOrderFlow(rows){const safe=Array.isArray(rows)?rows:[],bullish=safe.filter(r=>r.direction==="bullish").length,bearish=safe.filter(r=>r.direction==="bearish").length,unchanged=safe.filter(r=>r.direction==="unchanged").length,total=safe.length;return{bullish,bearish,unchanged,total,bullishShare:total?bullish/total:null,bearishShare:total?bearish/total:null};}
export function sortOrderFlow(rows,key="changePercent",direction="desc"){const sign=direction==="asc"?1:-1;return[...(rows||[])].sort((a,b)=>{if(key==="symbol")return String(a.symbol||"").localeCompare(String(b.symbol||""))*sign;const x=num(a[key]),y=num(b[key]);if(x===null&&y===null)return String(a.symbol||"").localeCompare(String(b.symbol||""));if(x===null)return 1;if(y===null)return-1;return(x-y)*sign;});}
export function buildChartFlowPoints(rows,limit=36){const safe=(Array.isArray(rows)?rows:[]).filter(r=>Number.isFinite(num(r.changePercent)));const ranked=[...safe].sort((a,b)=>Math.abs(b.changePercent)-Math.abs(a.changePercent)||a.symbol.localeCompare(b.symbol)).slice(0,Math.max(0,limit));const maxAbs=Math.max(0.1,...ranked.map(r=>Math.abs(r.changePercent)));return ranked.map((r,index)=>({...r,normalizedMove:r.changePercent/maxAbs,rank:index}));}


/** Organise the latest validated provider snapshot; this is not a full-exchange breadth estimate. */
export function buildMarketFlowBoard(rows, perSide = 12) {
  const safe = Array.isArray(rows) ? rows.filter(row => Number.isFinite(Number(row.changePercent))) : [];
  const bullish = safe.filter(row => row.changePercent > 0).sort((a, b) => b.changePercent - a.changePercent);
  const bearish = safe.filter(row => row.changePercent < 0).sort((a, b) => a.changePercent - b.changePercent);
  const unchanged = safe.filter(row => row.changePercent === 0).sort((a, b) => a.symbol.localeCompare(b.symbol));
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
    if (close === null || close <= 0 || timestamp === null || timestamp === undefined) return null;
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
