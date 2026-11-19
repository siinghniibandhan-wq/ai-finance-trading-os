const num=v=>{if(v===null||v===undefined||v==="")return null;const n=Number(v);return Number.isFinite(n)?n:null;};
export function normalizeOrderFlow(payload){const out=[];const source=payload?.market_movers||{};for(const key of ["gainers","losers"]){for(const row of Array.isArray(source[key])?source[key]:[]){const symbol=String(row?.symbol||"").trim().toUpperCase(),exchange=String(row?.exchange||"").trim().toUpperCase(),price=num(row?.ltp),changePercent=num(row?.percent_change);if(!symbol||!["NSE","BSE"].includes(exchange)||price===null||price<=0||changePercent===null)continue;out.push({symbol,exchange,name:String(row?.name||symbol),price,changePercent,volume:num(row?.volume),sector:typeof row?.sector==="string"&&row.sector.trim()?row.sector.trim():null,direction:changePercent>0?"bullish":changePercent<0?"bearish":"unchanged"});}}const unique=new Map();out.forEach(r=>unique.set(r.exchange+":"+r.symbol,r));return [...unique.values()];}
export function summarizeOrderFlow(rows){const safe=Array.isArray(rows)?rows:[],bullish=safe.filter(r=>r.direction==="bullish").length,bearish=safe.filter(r=>r.direction==="bearish").length,unchanged=safe.filter(r=>r.direction==="unchanged").length,total=safe.length;return{bullish,bearish,unchanged,total,bullishShare:total?bullish/total:null,bearishShare:total?bearish/total:null};}
export function sortOrderFlow(rows,key="changePercent",direction="desc"){const sign=direction==="asc"?1:-1;return[...(rows||[])].sort((a,b)=>{const x=num(a[key]),y=num(b[key]);if(x===null&&y===null)return a.symbol.localeCompare(b.symbol);if(x===null)return 1;if(y===null)return-1;return(x-y)*sign;});}
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


/** Validate provider OHLCV rows before passing them to a charting library. */
export function normalizeMarketFlowCandles(rows) {
  if (!Array.isArray(rows)) return [];
  const normalized = [];
  for (const row of rows) {
    if (!Array.isArray(row) || row.length < 5) continue;
    const rawTime = row[0];
    const numericTime = Number(rawTime);
    const parsedTime = Number.isFinite(numericTime) ? numericTime : Date.parse(String(rawTime));
    const time = Number.isFinite(parsedTime) ? Math.floor(parsedTime > 1e12 ? parsedTime / 1000 : parsedTime) : null;
    const open = num(row[1]);
    const high = num(row[2]);
    const low = num(row[3]);
    const close = num(row[4]);
    const volume = row.length > 5 ? num(row[5]) : null;
    if (!Number.isInteger(time) || time <= 0 ||
        [open, high, low, close].some(value => value === null || value <= 0) ||
        high < Math.max(open, close, low) || low > Math.min(open, close, high) ||
        (volume !== null && volume < 0)) continue;
    normalized.push({ time, open, high, low, close, volume });
  }
  return normalized.sort((a, b) => a.time - b.time)
    .filter((candle, index, all) => index === 0 || candle.time > all[index - 1].time);
}
