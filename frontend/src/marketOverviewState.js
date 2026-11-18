// Merge partial market refreshes without discarding the last successful value
// for a provider section that explicitly failed. Stale markers distinguish
// retained values from a fresh provider response.
export function mergeMarketOverview(previous, next) {
  if (!next || typeof next !== "object") return previous ?? null;

  const errors = Array.isArray(next.errors) ? next.errors : [];
  const previousIndices = Array.isArray(previous?.indices) ? previous.indices : [];
  const nextIndices = Array.isArray(next.indices) ? next.indices : [];
  const failedIndexNames = new Set(
    errors
      .filter((error) => error?.source === "market_indices" && error?.name)
      .map((error) => String(error.name).trim().toUpperCase())
  );
  const nextByName = new Map(
    nextIndices
      .filter((row) => row && row.name)
      .map((row) => [String(row.name).trim().toUpperCase(), row])
  );
  const staleIndexNames = [];
  const mergedIndices = [];
  const emitted = new Set();

  for (const oldRow of previousIndices) {
    if (!oldRow?.name) continue;
    const key = String(oldRow.name).trim().toUpperCase();
    const freshRow = nextByName.get(key);
    if (freshRow) {
      mergedIndices.push(freshRow);
      emitted.add(key);
    } else if (failedIndexNames.has(key)) {
      mergedIndices.push(oldRow);
      staleIndexNames.push(oldRow.name);
      emitted.add(key);
    }
  }

  for (const row of nextIndices) {
    if (!row || !row.name) {
      mergedIndices.push(row);
      continue;
    }
    const key = String(row.name).trim().toUpperCase();
    if (!emitted.has(key)) mergedIndices.push(row);
  }

  const previousMovers = previous?.market_movers || {};
  const nextMovers = next.market_movers || {};
  const failedMover = (type) => errors.some(
    (error) => error?.source === "market_movers" && String(error.type || "").toLowerCase() === type
  );
  const retainGainers = failedMover("gainers") && Array.isArray(previousMovers.gainers);
  const retainLosers = failedMover("losers") && Array.isArray(previousMovers.losers);

  return {
    ...next,
    indices: mergedIndices,
    market_movers: {
      ...previousMovers,
      ...nextMovers,
      gainers: retainGainers ? previousMovers.gainers : (Array.isArray(nextMovers.gainers) ? nextMovers.gainers : []),
      losers: retainLosers ? previousMovers.losers : (Array.isArray(nextMovers.losers) ? nextMovers.losers : []),
    },
    stale_sections: {
      indices: staleIndexNames,
      gainers: retainGainers,
      losers: retainLosers,
    },
  };
}
