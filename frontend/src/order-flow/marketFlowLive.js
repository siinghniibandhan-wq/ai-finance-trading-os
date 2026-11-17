export function getMarketFlowStatus(snapshot, requestError = "") {
  if (!snapshot || requestError) return "OFFLINE";
  const coverage = snapshot.coverage?.state;
  const feed = snapshot.feed?.status;
  const stream = snapshot.stream || {};
  if (feed === "fresh" && coverage === "ready") return "LIVE";
  if (feed === "stale") return "STALE";
  if (coverage === "starting" || ["connecting", "logging_in", "unconfirmed"].includes(stream.login_state)) return "CONNECTING";
  if (coverage === "auth_required" || coverage === "error") return "OFFLINE";
  if (coverage === "ready" && stream.running) return "CONNECTING";
  return "OFFLINE";
}

const finiteNonNegative = value =>
  typeof value === "number" && Number.isFinite(value) && value >= 0;

export function buildLiveMarketView(snapshot, symbol = "NIFTY") {
  const wanted = String(symbol || "NIFTY").toUpperCase();
  const futures = (Array.isArray(snapshot?.futures_contracts) ? snapshot.futures_contracts : [])
    .filter(row => String(row.symbol || "").toUpperCase() === wanted)
    .sort((a, b) => String(a.expiry || "").localeCompare(String(b.expiry || "")))
    .map(row => ({
      symbol: row.symbol,
      tradingsymbol: row.tradingsymbol,
      expiry: row.expiry,
      price: finiteNonNegative(row.price) && row.price > 0 ? row.price : null,
      oi: finiteNonNegative(row.oi) ? row.oi : null,
      volume: finiteNonNegative(row.volume) ? row.volume : null,
    }));
  const strikes = Array.isArray(snapshot?.option_oi_by_strike)
    ? snapshot.option_oi_by_strike.filter(row =>
        finiteNonNegative(row.strike) &&
        finiteNonNegative(row.ce_oi) &&
        finiteNonNegative(row.pe_oi))
      .sort((a, b) => a.strike - b.strike)
    : [];
  const callTotal = strikes.reduce((sum, row) => sum + row.ce_oi, 0);
  const putTotal = strikes.reduce((sum, row) => sum + row.pe_oi, 0);
  const maxCall = strikes.length ? strikes.reduce((best, row) => row.ce_oi > best.ce_oi ? row : best) : null;
  const maxPut = strikes.length ? strikes.reduce((best, row) => row.pe_oi > best.pe_oi ? row : best) : null;
  const unavailable = Array.isArray(snapshot?.coverage?.unavailable)
    ? snapshot.coverage.unavailable.filter(row =>
        !row.tradingsymbol || String(row.tradingsymbol).toUpperCase().startsWith(wanted))
    : [];
  return {
    symbol: wanted,
    futures,
    strikes,
    pcr: callTotal > 0 ? putTotal / callTotal : null,
    support: maxPut ? { strike: maxPut.strike, oi: maxPut.pe_oi } : null,
    resistance: maxCall ? { strike: maxCall.strike, oi: maxCall.ce_oi } : null,
    unavailable,
    asOf: snapshot?.feed?.last_tick_at || snapshot?.as_of || null,
    previousOiAvailable: snapshot?.historical_oi_included === true,
  };
}

export function formatMarketValue(value, digits = 2) {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("en-IN", { maximumFractionDigits: digits }).format(value)
    : "Unavailable";
}
