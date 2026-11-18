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
 * Convert the m.Stock historical candle tuple
 * [timestamp, open, high, low, close, volume] into chart-library data.
 * Invalid provider rows are omitted; no values are inferred or filled.
 */
export function normalizeCandles(rawCandles) {
  if (!Array.isArray(rawCandles)) return [];

  const byTime = new Map();
  for (const row of rawCandles) {
    if (!Array.isArray(row) || row.length < 6) continue;
    const time = toUnixSeconds(row[0]);
    const open = finiteNumber(row[1]);
    const high = finiteNumber(row[2]);
    const low = finiteNumber(row[3]);
    const close = finiteNumber(row[4]);
    const volume = finiteNumber(row[5]);

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

export function toVolumeSeries(candles) {
  return candles.map(({ time, close, volume }) => ({
    time,
    value: volume,
    color: close >= 0 ? undefined : undefined,
  }));
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
