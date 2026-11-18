const finiteNumber = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const cleanSymbol = (value) => String(value || "").trim().toUpperCase();

export function buildLiveOrderFlow(snapshot, selectedSymbol = "") {
  const selected = cleanSymbol(selectedSymbol);
  const usable = snapshot?.status === "success" && snapshot?.feed?.status === "fresh";
  if (!usable) {
    return {
      isLive: false,
      feed: snapshot?.feed || { status: "disconnected", last_tick_at: null, age_seconds: null },
      stream: snapshot?.stream || {},
      futures: [],
      options: [],
      optionOiByStrike: [],
      underlyings: [],
      asOf: null,
      coverage: snapshot?.coverage || {},
    };
  }

  const matches = (row) => !selected || cleanSymbol(row?.symbol) === selected;
  const futures = (Array.isArray(snapshot.futures_contracts) ? snapshot.futures_contracts : [])
    .filter(matches)
    .map((row) => ({
      symbol: cleanSymbol(row.symbol),
      contract: String(row.tradingsymbol || ""),
      exchange: String(row.exchange || ""),
      expiry: String(row.expiry || ""),
      price: finiteNumber(row.price),
      volume: finiteNumber(row.volume),
      oi: finiteNumber(row.oi),
      receivedAt: row.received_at || null,
      exchangeTimestamp: row.exchange_timestamp || null,
    }))
    .filter((row) => row.symbol && row.price !== null && row.price > 0)
    .sort((a, b) => a.symbol.localeCompare(b.symbol) || a.expiry.localeCompare(b.expiry));

  const options = (Array.isArray(snapshot.option_contracts) ? snapshot.option_contracts : [])
    .filter(matches)
    .map((row) => ({
      symbol: cleanSymbol(row.symbol),
      contract: String(row.tradingsymbol || ""),
      exchange: String(row.exchange || ""),
      expiry: String(row.expiry || ""),
      strike: finiteNumber(row.strike),
      optionType: String(row.option_type || "").toUpperCase(),
      price: finiteNumber(row.price),
      volume: finiteNumber(row.volume),
      oi: finiteNumber(row.oi),
      receivedAt: row.received_at || null,
      exchangeTimestamp: row.exchange_timestamp || null,
    }))
    .filter((row) => row.symbol && row.strike !== null && row.strike > 0 &&
      ["CE", "PE"].includes(row.optionType) && row.oi !== null)
    .sort((a, b) => a.symbol.localeCompare(b.symbol) ||
      a.expiry.localeCompare(b.expiry) || a.strike - b.strike ||
      a.optionType.localeCompare(b.optionType));

  const optionOiByStrike = (Array.isArray(snapshot.option_oi_by_strike) ? snapshot.option_oi_by_strike : [])
    .map((row) => ({
      strike: finiteNumber(row?.strike),
      callOi: finiteNumber(row?.ce_oi),
      putOi: finiteNumber(row?.pe_oi),
    }))
    .filter((row) => row.strike !== null && row.strike > 0 &&
      (row.callOi !== null || row.putOi !== null))
    .sort((a, b) => a.strike - b.strike);

  const underlyings = [...new Set([
    ...futures.map((row) => row.symbol),
    ...options.map((row) => row.symbol),
  ])].sort();

  return {
    isLive: true,
    feed: snapshot.feed,
    stream: snapshot.stream || {},
    futures,
    options,
    optionOiByStrike,
    underlyings,
    asOf: snapshot.as_of || snapshot.feed?.last_tick_at || null,
    coverage: snapshot.coverage || {},
  };
}

export function formatMarketNumber(value) {
  const number = finiteNumber(value);
  return number === null ? "—" : new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(number);
}

export function formatMarketTimestamp(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "Asia/Kolkata",
  });
}
