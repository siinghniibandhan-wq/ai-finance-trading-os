const finite = value => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const nonNegative = value => {
  const parsed = finite(value);
  return parsed !== null && parsed >= 0 ? parsed : null;
};

/** Normalize only actual CE/PE contracts returned by the provider gateway. */
export function buildOptionChainRows(contracts) {
  const byStrike = new Map();
  for (const contract of Array.isArray(contracts) ? contracts : []) {
    const strike = finite(contract?.strike);
    const side = String(contract?.side || "").trim().toUpperCase();
    if (strike === null || strike <= 0 || !["CE", "PE"].includes(side)) continue;
    const row = byStrike.get(strike) || { strike, CE: null, PE: null };
    const normalized = {
      symbol: String(contract?.tradingsymbol || ""),
      lastPrice: finite(contract?.last_price),
      volume: nonNegative(contract?.volume),
      openInterest: nonNegative(contract?.open_interest),
      lotSize: nonNegative(contract?.lot_size),
      quoteAvailable: contract?.quote_available === true,
    };
    row[side] = normalized;
    byStrike.set(strike, row);
  }
  return [...byStrike.values()].sort((a, b) => a.strike - b.strike);
}

/**
 * OI analytics are enabled only for a complete two-sided strike sample.
 * Missing CE/PE contracts or OI values must not produce PCR or Max Pain.
 */
export function calculateOptionsAnalytics(contracts) {
  const rows = buildOptionChainRows(contracts);
  const completeOI = rows.length > 0 && rows.every(row =>
    row.CE && row.PE &&
    row.CE.openInterest !== null &&
    row.PE.openInterest !== null
  );
  if (!completeOI) {
    return {
      rows,
      oiComplete: false,
      callOI: null,
      putOI: null,
      pcr: null,
      maxPain: null,
    };
  }

  const callOI = rows.reduce((sum, row) => sum + row.CE.openInterest, 0);
  const putOI = rows.reduce((sum, row) => sum + row.PE.openInterest, 0);
  const pcr = callOI > 0 ? putOI / callOI : null;

  const painBySettlement = rows.map(settlement => {
    const pain = rows.reduce((sum, row) => {
      const callPain = row.CE.openInterest * Math.max(0, settlement.strike - row.strike);
      const putPain = row.PE.openInterest * Math.max(0, row.strike - settlement.strike);
      return sum + callPain + putPain;
    }, 0);
    return { strike: settlement.strike, pain };
  });
  const maxPain = painBySettlement.reduce((best, current) =>
    current.pain < best.pain ? current : best
  , painBySettlement[0]).strike;

  return { rows, oiComplete: true, callOI, putOI, pcr, maxPain };
}

/** Return a mirrored chart scale based only on verified OI observations. */
export function buildOptionOIBars(rows, width = 420) {
  const valid = (Array.isArray(rows) ? rows : []).filter(row =>
    row?.CE?.openInterest !== null && row?.CE?.openInterest !== undefined &&
    row?.PE?.openInterest !== null && row?.PE?.openInterest !== undefined
  );
  if (!valid.length) return [];
  const max = Math.max(1, ...valid.flatMap(row => [row.CE.openInterest, row.PE.openInterest]));
  return valid.map(row => ({
    strike: row.strike,
    callWidth: row.CE.openInterest / max * width,
    putWidth: row.PE.openInterest / max * width,
    callOI: row.CE.openInterest,
    putOI: row.PE.openInterest,
  }));
}
