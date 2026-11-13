export function toSpotChangeRows(series) {
  if (!Array.isArray(series)) return [];
  return series.map((item) => {
    const spot = Number(item?.sp);
    const previousClose = Number(item?.pc);
    return {
      symbol: item?.s || item?.symbol,
      change: Number.isFinite(spot) && Number.isFinite(previousClose) && previousClose > 0
        ? ((spot - previousClose) / previousClose) * 100
        : null,
    };
  }).filter((item) => item.symbol && item.change !== null)
    .sort((a, b) => b.change - a.change);
}
