const toUnixSeconds = (value) => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.floor(value > 1e12 ? value / 1000 : value);
  }
  if (typeof value !== "string" || !value.trim()) return null;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : null;
};

const finiteNumber = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

/**
 * Convert either the Market Charts API candle object
 * { timestamp, open, high, low, close, volume } or the underlying
 * m.Stock tuple [timestamp, open, high, low, close, volume]
 * into chart-library data. Invalid rows are omitted; no values are inferred.
 */
export function normalizeCandles(rawCandles) {
  if (!Array.isArray(rawCandles)) return [];

  const byTime = new Map();
  for (const row of rawCandles) {
    const isTuple = Array.isArray(row);
    if (isTuple && row.length < 6) continue;
    if (!isTuple && (!row || typeof row !== "object")) continue;

    const time = toUnixSeconds(isTuple ? row[0] : row.timestamp);
    const open = finiteNumber(isTuple ? row[1] : row.open);
    const high = finiteNumber(isTuple ? row[2] : row.high);
    const low = finiteNumber(isTuple ? row[3] : row.low);
    const close = finiteNumber(isTuple ? row[4] : row.close);
    const volume = finiteNumber(isTuple ? row[5] : row.volume);

    if (
      time === null ||
      [open, high, low, close, volume].some((value) => value === null) ||
      open <= 0 || high <= 0 || low <= 0 || close <= 0 || volume < 0 ||
      high < Math.max(open, close, low) ||
      low > Math.min(open, close, high)
    ) continue;

    byTime.set(time, { time, open, high, low, close, volume });
  }

  return [...byTime.values()].sort((a, b) => a.time - b.time);
}

export function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getDefaultChartRange(now = new Date(), calendarDays = 5) {
  const to = new Date(now);
  const from = new Date(now);
  from.setDate(from.getDate() - calendarDays);
  return { from: formatLocalDate(from), to: formatLocalDate(to) };
}
