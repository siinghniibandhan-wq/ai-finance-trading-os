/**
 * Overlays REAL m.Stock values onto the existing Market Flow stocks.
 * Only price, volume, open interest and option OI by strike are replaced,
 * and only when the gateway snapshot is fresh. Everything else (change %,
 * candles, build-up, support/resistance, PCR, conviction) is left untouched
 * and stays labelled simulated. Nothing is invented.
 */
const num = v => {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};

export function isFreshSnapshot(snapshot) {
  return !!snapshot && snapshot.status === "success" && snapshot.feed?.status === "fresh";
}

const expiryKey = e => {
  const t = Date.parse(e);
  return Number.isFinite(t) ? t : Number.POSITIVE_INFINITY;
};

export function nearestFutures(snapshot) {
  const best = new Map();
  const list = Array.isArray(snapshot?.futures_contracts) ? snapshot.futures_contracts : [];
  for (const item of list) {
    const symbol = String(item?.symbol || "").trim().toUpperCase();
    const price = num(item?.price);
    if (!symbol || price === null || price <= 0) continue;
    const row = { symbol, price, volume: num(item.volume), oi: num(item.oi), expiry: String(item.expiry || ""), contract: String(item.tradingsymbol || "") };
    const cur = best.get(symbol);
    if (!cur || expiryKey(row.expiry) < expiryKey(cur.expiry)) best.set(symbol, row);
  }
  return best;
}

export function overlayLiveData(stocks, snapshot, optionSymbol) {
  if (!Array.isArray(stocks) || !isFreshSnapshot(snapshot)) return stocks;
  const futures = nearestFutures(snapshot);
  const strikes = (Array.isArray(snapshot.option_oi_by_strike) ? snapshot.option_oi_by_strike : [])
    .map(s => ({ strike: num(s?.strike), call: num(s?.ce_oi), put: num(s?.pe_oi) }))
    .filter(s => s.strike !== null && s.call !== null && s.put !== null)
    .sort((a, b) => a.strike - b.strike);
  return stocks.map(stock => {
    const live = futures.get(String(stock.symbol).toUpperCase());
    const useStrikes = strikes.length > 0 && optionSymbol && stock.symbol === optionSymbol;
    if (!live && !useStrikes) return stock;
    const next = { ...stock };
    if (live) {
      next.future = live.price;
      if (live.oi !== null) next.oi = live.oi;
      next.liveVolume = live.volume;
      next.liveContract = live.contract;
      next.live = true;
    }
    if (useStrikes) {
      next.strikes = strikes;
      next.strikesLive = true;
    }
    return next;
  });
}

export function countLive(stocks) {
  return Array.isArray(stocks) ? stocks.filter(s => s.live).length : 0;
}
