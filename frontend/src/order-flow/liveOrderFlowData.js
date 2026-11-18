const finite = (value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));

/**
 * Overlay only verified, fresh NFO futures and option OI onto the existing demo
 * universe. Demo-derived percentage changes, candles, signals and levels remain
 * untouched because the snapshot does not contain the history needed to derive them.
 */
export function mapLiveOrderFlowSnapshot(snapshot, stocks) {
  if (!Array.isArray(stocks)) throw new TypeError("stocks must be an array");
  const feed = snapshot?.feed;
  const fresh = snapshot?.status === "success" && feed?.status === "fresh";
  if (!fresh) return { feedStatus: feed?.status || "disconnected", isLive: false, stocks };

  const futures = Array.isArray(snapshot.futures_contracts) ? snapshot.futures_contracts : [];
  const options = Array.isArray(snapshot.option_contracts) ? snapshot.option_contracts : [];
  const optionOi = Array.isArray(snapshot.option_oi_by_strike) ? snapshot.option_oi_by_strike : [];
  const bySymbol = new Map();

  for (const contract of futures) {
    const symbol = String(contract?.symbol || "").trim().toUpperCase();
    const exchange = String(contract?.exchange || "").trim().toUpperCase();
    if (!symbol || exchange !== "NFO" || !finite(contract?.price)) continue;
    const previous = bySymbol.get(symbol);
    if (!previous || String(contract.expiry || "") < String(previous.expiry || "")) {
      bySymbol.set(symbol, {
        contract: contract.tradingsymbol || null,
        expiry: contract.expiry || null,
        price: Number(contract.price),
        volume: finite(contract.volume) ? Number(contract.volume) : null,
        oi: finite(contract.oi) ? Number(contract.oi) : null,
        exchange,
        instrumentToken: contract.instrument_token ?? null,
      });
    }
  }

  const strikesBySymbol = new Map();
  for (const row of optionOi) {
    if (!finite(row?.strike)) continue;
    const strike = Number(row.strike);
    const key = String(row.symbol || "").trim().toUpperCase();
    if (!key) continue;
    const rows = strikesBySymbol.get(key) || new Map();
    rows.set(strike, {
      strike,
      put: finite(row.pe_oi) ? Number(row.pe_oi) : 0,
      call: finite(row.ce_oi) ? Number(row.ce_oi) : 0,
    });
    strikesBySymbol.set(key, rows);
  }
  // The aggregate endpoint currently omits underlying identity; only use the
  // requested underlying's raw option contracts when building its strike profile.
  for (const contract of options) {
    const symbol = String(contract?.symbol || "").trim().toUpperCase();
    const exchange = String(contract?.exchange || "").trim().toUpperCase();
    if (!symbol || exchange !== "NFO" || !finite(contract?.strike) || !finite(contract?.oi)) continue;
    const rows = strikesBySymbol.get(symbol) || new Map();
    const strike = Number(contract.strike);
    const row = rows.get(strike) || { strike, put: 0, call: 0 };
    if (String(contract.option_type).toUpperCase() === "PE") row.put = Number(contract.oi);
    if (String(contract.option_type).toUpperCase() === "CE") row.call = Number(contract.oi);
    rows.set(strike, row);
    strikesBySymbol.set(symbol, rows);
  }

  const mappedStocks = stocks.map((stock) => {
    const symbol = String(stock.symbol || "").trim().toUpperCase();
    const live = bySymbol.get(symbol);
    if (!live) return stock;
    const liveStrikes = strikesBySymbol.get(symbol);
    return {
      ...stock,
      liveMarket: {
        ...live,
        strikes: liveStrikes ? [...liveStrikes.values()].sort((a, b) => a.strike - b.strike) : [],
        asOf: snapshot.as_of || null,
      },
    };
  });
  return {
    feedStatus: "fresh",
    isLive: bySymbol.size > 0,
    stocks: mappedStocks,
    mappedFutures: bySymbol.size,
  };
}
