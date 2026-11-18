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

export function getChartDimensions(width, height) {
  const safeWidth = Number.isFinite(width) && width > 0 ? Math.max(width, 320) : 320;
  const safeHeight = Number.isFinite(height) && height > 0 ? height : 520;
  return { width: safeWidth, height: safeHeight };
}

export function calculateSMA(candles, period = 20) {
  if (!Array.isArray(candles) || !Number.isInteger(period) || period < 1 || candles.length < period) return [];
  const points = [];
  let sum = 0;
  for (let index = 0; index < candles.length; index += 1) {
    const close = candles[index]?.close;
    if (!Number.isFinite(close)) return [];
    sum += close;
    if (index >= period) sum -= candles[index - period].close;
    if (index >= period - 1) {
      points.push({ time: candles[index].time, value: sum / period });
    }
  }
  return points;
}

export function calculateEMA(candles, period = 20) {
  if (!Array.isArray(candles) || !Number.isInteger(period) || period < 1 || candles.length < period) return [];
  const initialWindow = candles.slice(0, period);
  if (initialWindow.some((candle) => !Number.isFinite(candle?.close))) return [];
  let ema = initialWindow.reduce((sum, candle) => sum + candle.close, 0) / period;
  const points = [{ time: initialWindow[period - 1].time, value: ema }];
  const multiplier = 2 / (period + 1);

  for (let index = period; index < candles.length; index += 1) {
    const candle = candles[index];
    if (!Number.isFinite(candle?.close)) return [];
    ema = (candle.close - ema) * multiplier + ema;
    points.push({ time: candle.time, value: ema });
  }
  return points;
}

export function formatChartTime(time) {
  if (time && typeof time === "object" &&
      Number.isInteger(time.year) && Number.isInteger(time.month) && Number.isInteger(time.day)) {
    return `${String(time.day).padStart(2, "0")}/${String(time.month).padStart(2, "0")}/${time.year}`;
  }
  if (typeof time === "number" && Number.isFinite(time)) {
    return new Date(time * 1000).toLocaleString("en-IN");
  }
  return "—";
}


/**
 * Read the latest traded price from the authenticated Market Quote API response.
 * Invalid, zero and missing values are intentionally treated as unavailable.
 */
export function normalizeQuotePrice(payload) {
  const value = payload?.quote?.last_price;
  if (value === null || value === undefined || value === "") return null;
  const price = Number(value);
  return Number.isFinite(price) && price > 0 ? price : null;
}
