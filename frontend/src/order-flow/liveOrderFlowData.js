const finiteNumber = value => {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const safeArray = (value, label) => {
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value)) throw new TypeError("Invalid " + label + " collection.");
  return value;
};

/**
 * Converts the authenticated Order Flow API response into display-only rows.
 * Deliberately does not manufacture spot changes, candles, PCR, support,
 * resistance, conviction, or OI change when the provider has not supplied them.
 */
export function mapLiveOrderFlowSnapshot(snapshot) {
  if (!snapshot || snapshot.status !== "success") {
    throw new TypeError("Invalid live Order Flow snapshot.");
  }
  const futures = safeArray(snapshot.futures_contracts, "futures").map(item => ({
    symbol: String(item.symbol || "").trim().toUpperCase(),
    contract: String(item.tradingsymbol || "").trim(),
    expiry: String(item.expiry || ""),
    price: finiteNumber(item.price),
    volume: finiteNumber(item.volume),
    oi: finiteNumber(item.oi),
    exchange: String(item.exchange || ""),
  })).filter(item => item.symbol && item.contract);

  const options = safeArray(snapshot.option_contracts, "options").map(item => ({
    symbol: String(item.symbol || "").trim().toUpperCase(),
    contract: String(item.tradingsymbol || "").trim(),
    expiry: String(item.expiry || ""),
    strike: finiteNumber(item.strike),
    optionType: item.option_type === "CE" || item.option_type === "PE" ? item.option_type : null,
    price: finiteNumber(item.price),
    volume: finiteNumber(item.volume),
    oi: finiteNumber(item.oi),
  })).filter(item => item.symbol && item.contract && item.strike !== null && item.optionType);

  const optionOi = safeArray(snapshot.option_oi_by_strike, "option OI").map(item => ({
    strike: finiteNumber(item.strike),
    ceOi: finiteNumber(item.ce_oi),
    peOi: finiteNumber(item.pe_oi),
  })).filter(item => item.strike !== null).sort((a, b) => a.strike - b.strike);

  futures.sort((a, b) => a.symbol.localeCompare(b.symbol) || a.expiry.localeCompare(b.expiry));
  options.sort((a, b) => a.symbol.localeCompare(b.symbol) || a.expiry.localeCompare(b.expiry) || a.strike - b.strike || a.optionType.localeCompare(b.optionType));

  return {
    feedStatus: snapshot.feed?.status || "disconnected",
    ageSeconds: finiteNumber(snapshot.feed?.age_seconds),
    asOf: snapshot.as_of || snapshot.feed?.last_tick_at || null,
    source: snapshot.source || "m.Stock market-stream gateway",
    futures,
    options,
    optionOi,
    coverage: snapshot.coverage || null,
  };
}
