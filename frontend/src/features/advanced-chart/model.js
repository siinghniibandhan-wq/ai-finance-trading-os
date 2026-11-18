const toUnixSeconds = (value) => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.floor(value > 1e12 ? value / 1000 : value);
  }
  if (typeof value !== "string" || !value.trim()) return null;
  const trimmed = value.trim();
  if (/^\d+(?:\.\d+)?$/.test(trimmed)) {
    const numeric = Number(trimmed);
    return Number.isFinite(numeric)
      ? Math.floor(numeric > 1e12 ? numeric / 1000 : numeric)
      : null;
  }
  const parsed = Date.parse(trimmed);
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
      [open, high, low, close].some((value) => value === null) ||
      open <= 0 || high <= 0 || low <= 0 || close <= 0 ||
      (volume !== null && volume < 0) ||
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


/** Build the existing Market Search API query without changing its contract. */
export function buildInstrumentSearchParams(query, exchange = "ALL") {
  const selectedExchange = ["ALL", "NSE", "BSE"].includes(String(exchange).toUpperCase())
    ? String(exchange).toUpperCase()
    : "ALL";
  return new URLSearchParams({
    query: String(query ?? "").trim(),
    exchange: selectedExchange,
    limit: "20",
    product_type: "Stocks",
  });
}

/**
 * Derive Heikin-Ashi display candles from validated provider OHLC candles.
 * Source candles remain unchanged; no price observations are invented.
 */
export function calculateHeikinAshi(candles) {
  if (!Array.isArray(candles) || !candles.length) return [];
  const result = [];
  let previousOpen = null;
  let previousClose = null;
  for (const candle of candles) {
    const { time, open, high, low, close } = candle || {};
    if (!Number.isFinite(time) || [open, high, low, close].some((value) => !Number.isFinite(value)) ||
        open <= 0 || high < Math.max(open, close, low) || low > Math.min(open, close, high)) return [];
    const haClose = (open + high + low + close) / 4;
    const haOpen = previousOpen === null ? (open + close) / 2 : (previousOpen + previousClose) / 2;
    const point = {
      time,
      open: haOpen,
      high: Math.max(high, haOpen, haClose),
      low: Math.min(low, haOpen, haClose),
      close: haClose,
    };
    result.push(point);
    previousOpen = haOpen;
    previousClose = haClose;
  }
  return result;
}

function emaValues(values, period) {
  if (!Array.isArray(values) || values.length < period || !Number.isInteger(period) || period < 1 ||
      values.some((value) => !Number.isFinite(value))) return [];
  const multiplier = 2 / (period + 1);
  let ema = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
  const output = Array(period - 1).fill(null);
  output.push(ema);
  for (let index = period; index < values.length; index += 1) {
    ema = (values[index] - ema) * multiplier + ema;
    output.push(ema);
  }
  return output;
}

export function calculateRSI(candles, period = 14) {
  if (!Array.isArray(candles) || !Number.isInteger(period) || period < 1 ||
      candles.length <= period || candles.some((candle) => !Number.isFinite(candle?.close))) return [];
  let gains = 0;
  let losses = 0;
  for (let index = 1; index <= period; index += 1) {
    const change = candles[index].close - candles[index - 1].close;
    gains += Math.max(change, 0);
    losses += Math.max(-change, 0);
  }
  let averageGain = gains / period;
  let averageLoss = losses / period;
  const output = [];
  const value = () => averageLoss === 0 ? (averageGain === 0 ? 50 : 100)
    : 100 - 100 / (1 + averageGain / averageLoss);
  output.push({ time: candles[period].time, value: value() });
  for (let index = period + 1; index < candles.length; index += 1) {
    const change = candles[index].close - candles[index - 1].close;
    averageGain = (averageGain * (period - 1) + Math.max(change, 0)) / period;
    averageLoss = (averageLoss * (period - 1) + Math.max(-change, 0)) / period;
    output.push({ time: candles[index].time, value: value() });
  }
  return output;
}

export function calculateMACD(candles, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
  if (!Array.isArray(candles) || fastPeriod >= slowPeriod ||
      candles.some((candle) => !Number.isFinite(candle?.close))) {
    return { macd: [], signal: [], histogram: [] };
  }
  const closes = candles.map((candle) => candle.close);
  const fast = emaValues(closes, fastPeriod);
  const slow = emaValues(closes, slowPeriod);
  const raw = [];
  for (let index = 0; index < candles.length; index += 1) {
    if (fast[index] !== null && slow[index] !== null) {
      raw.push({ time: candles[index].time, value: fast[index] - slow[index] });
    }
  }
  const signalValues = emaValues(raw.map((point) => point.value), signalPeriod);
  const macd = raw.slice(signalPeriod - 1);
  const signal = macd.map((point, index) => ({ time: point.time, value: signalValues[index + signalPeriod - 1] }));
  const histogram = macd.map((point, index) => ({ time: point.time, value: point.value - signal[index].value }));
  return { macd, signal, histogram };
}

export function calculateBollingerBands(candles, period = 20, multiplier = 2) {
  if (!Array.isArray(candles) || !Number.isInteger(period) || period < 1 ||
      !Number.isFinite(multiplier) || multiplier <= 0 || candles.length < period ||
      candles.some((candle) => !Number.isFinite(candle?.close))) {
    return { upper: [], middle: [], lower: [] };
  }
  const upper = [];
  const middle = [];
  const lower = [];
  for (let index = period - 1; index < candles.length; index += 1) {
    const window = candles.slice(index - period + 1, index + 1).map((candle) => candle.close);
    const mean = window.reduce((sum, value) => sum + value, 0) / period;
    const variance = window.reduce((sum, value) => sum + (value - mean) ** 2, 0) / period;
    const deviation = Math.sqrt(variance);
    const time = candles[index].time;
    middle.push({ time, value: mean });
    upper.push({ time, value: mean + multiplier * deviation });
    lower.push({ time, value: mean - multiplier * deviation });
  }
  return { upper, middle, lower };
}

export function calculateVWAP(candles) {
  if (!Array.isArray(candles) || !candles.length ||
      candles.some((candle) => !Number.isFinite(candle?.high) ||
        !Number.isFinite(candle?.low) || !Number.isFinite(candle?.close) ||
        !Number.isFinite(candle?.volume) || candle.volume <= 0)) return [];
  let cumulativePriceVolume = 0;
  let cumulativeVolume = 0;
  return candles.map((candle) => {
    const typicalPrice = (candle.high + candle.low + candle.close) / 3;
    cumulativePriceVolume += typicalPrice * candle.volume;
    cumulativeVolume += candle.volume;
    return { time: candle.time, value: cumulativePriceVolume / cumulativeVolume };
  });
}
