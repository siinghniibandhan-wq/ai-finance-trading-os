const finite = (value) =>
  value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));

/**
 * Build Market Flow only from fresh m.Stock derivative contracts.
 * No demo universe or simulated analytics are supplied as a fallback.
 */
export function mapLiveOrderFlowSnapshot(snapshot) {
  const feed = snapshot?.feed;
  const fresh = snapshot?.status === "success" && feed?.status === "fresh";
  if (!fresh) {
    return {
      feedStatus: feed?.status || "disconnected",
      isLive: false,
      stocks: [],
      futuresCount: 0,
      optionsCount: 0,
      asOf: null,
    };
  }

  const options = Array.isArray(snapshot.option_contracts) ? snapshot.option_contracts : [];
  const strikesBySymbol = new Map();

  for (const contract of options) {
    const symbol = String(contract?.symbol || "").trim().toUpperCase();
    const exchange = String(contract?.exchange || "").trim().toUpperCase();
    if (!symbol || exchange !== "NFO" || !finite(contract?.strike) || !finite(contract?.oi)) continue;

    const strike = Number(contract.strike);
    const rows = strikesBySymbol.get(symbol) || new Map();
    const row = rows.get(strike) || { strike, put: 0, call: 0 };
    const optionType = String(contract.option_type || "").trim().toUpperCase();
    if (optionType === "PE") row.put = Number(contract.oi);
    if (optionType === "CE") row.call = Number(contract.oi);
    rows.set(strike, row);
    strikesBySymbol.set(symbol, rows);
  }

  const futures = Array.isArray(snapshot.futures_contracts) ? snapshot.futures_contracts : [];
  const byContract = new Map();

  for (const contract of futures) {
    const symbol = String(contract?.symbol || "").trim().toUpperCase();
    const exchange = String(contract?.exchange || "").trim().toUpperCase();
    if (!symbol || exchange !== "NFO" || !finite(contract?.price) || Number(contract.price) <= 0) continue;

    const expiry = String(contract.expiry || "");
    const key = symbol + ":" + expiry;
    byContract.set(key, {
      symbol,
      contract: contract.tradingsymbol || key,
      expiry: expiry || null,
      exchange,
      instrumentToken: contract.instrument_token ?? null,
      price: Number(contract.price),
      previousClose: finite(contract.previous_close) && Number(contract.previous_close) > 0
        ? Number(contract.previous_close)
        : null,
      changePct: finite(contract.previous_close) && Number(contract.previous_close) > 0
        ? ((Number(contract.price) - Number(contract.previous_close)) / Number(contract.previous_close)) * 100
        : null,
      volume: finite(contract.volume) ? Number(contract.volume) : null,
      oi: finite(contract.oi) ? Number(contract.oi) : null,
      averageTradedPrice: finite(contract.average_traded_price) ? Number(contract.average_traded_price) : null,
      exchangeTimestamp: contract.exchange_timestamp || null,
      receivedAt: contract.received_at || null,
      strikes: [...(strikesBySymbol.get(symbol)?.values() || [])].sort((a, b) => a.strike - b.strike),
      source: "m.Stock",
    });
  }

  const stocks = [...byContract.values()].sort((a, b) =>
    a.symbol.localeCompare(b.symbol) || String(a.expiry || "").localeCompare(String(b.expiry || ""))
  );

  return {
    feedStatus: stocks.length ? "fresh" : "no_live_contracts",
    isLive: stocks.length > 0,
    stocks,
    futuresCount: stocks.length,
    optionsCount: options.filter((item) => item?.exchange === "NFO").length,
    asOf: snapshot.as_of || null,
  };
}
