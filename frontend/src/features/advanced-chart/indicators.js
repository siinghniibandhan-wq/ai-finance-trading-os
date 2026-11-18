const validPeriod = (period) => Number.isInteger(period) && period > 0;
const validPositive = (value) => Number.isFinite(value) && value > 0;

function emaValues(values, period) {
  if (!validPeriod(period) || values.length < period || values.some((value) => !Number.isFinite(value))) return [];
  const seed = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
  const result = [seed];
  const multiplier = 2 / (period + 1);
  for (let index = period; index < values.length; index += 1) {
    result.push((values[index] - result[result.length - 1]) * multiplier + result[result.length - 1]);
  }
  return result;
}

export function calculateRSI(candles, period = 14) {
  if (!Array.isArray(candles) || !validPeriod(period) || candles.length <= period) return [];
  const closes = candles.map((candle) => candle?.close);
  if (closes.some((value) => !validPositive(value))) return [];
  let gains = 0;
  let losses = 0;
  for (let index = 1; index <= period; index += 1) {
    const change = closes[index] - closes[index - 1];
    gains += Math.max(change, 0);
    losses += Math.max(-change, 0);
  }
  let averageGain = gains / period;
  let averageLoss = losses / period;
  const toRsi = () => averageLoss === 0
    ? (averageGain === 0 ? 50 : 100)
    : 100 - (100 / (1 + averageGain / averageLoss));
  const points = [{ time: candles[period].time, value: toRsi() }];
  for (let index = period + 1; index < candles.length; index += 1) {
    const change = closes[index] - closes[index - 1];
    averageGain = (averageGain * (period - 1) + Math.max(change, 0)) / period;
    averageLoss = (averageLoss * (period - 1) + Math.max(-change, 0)) / period;
    points.push({ time: candles[index].time, value: toRsi() });
  }
  return points;
}

export function calculateATR(candles, period = 14) {
  if (!Array.isArray(candles) || !validPeriod(period) || candles.length <= period) return [];
  const ranges = [];
  for (let index = 1; index < candles.length; index += 1) {
    const current = candles[index];
    const previous = candles[index - 1];
    if (![current?.high, current?.low, previous?.close].every(validPositive) || current.high < current.low) return [];
    ranges.push(Math.max(
      current.high - current.low,
      Math.abs(current.high - previous.close),
      Math.abs(current.low - previous.close),
    ));
  }
  if (ranges.some((value) => !Number.isFinite(value))) return [];
  let atr = ranges.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
  const points = [{ time: candles[period].time, value: atr }];
  for (let index = period; index < ranges.length; index += 1) {
    atr = (atr * (period - 1) + ranges[index]) / period;
    points.push({ time: candles[index + 1].time, value: atr });
  }
  return points;
}

export function calculateBollingerBands(candles, period = 20, multiplier = 2) {
  if (!Array.isArray(candles) || !validPeriod(period) || !Number.isFinite(multiplier) || multiplier <= 0 || candles.length < period) return [];
  const points = [];
  for (let index = period - 1; index < candles.length; index += 1) {
    const window = candles.slice(index - period + 1, index + 1).map((candle) => candle?.close);
    if (window.some((value) => !validPositive(value))) return [];
    const middle = window.reduce((sum, value) => sum + value, 0) / period;
    const variance = window.reduce((sum, value) => sum + ((value - middle) ** 2), 0) / period;
    const deviation = Math.sqrt(variance) * multiplier;
    points.push({ time: candles[index].time, upper: middle + deviation, middle, lower: middle - deviation });
  }
  return points;
}

export function calculateMACD(candles, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
  if (!Array.isArray(candles) || !validPeriod(fastPeriod) || !validPeriod(slowPeriod) ||
      !validPeriod(signalPeriod) || fastPeriod >= slowPeriod || candles.length < slowPeriod + signalPeriod - 1) return [];
  const closes = candles.map((candle) => candle?.close);
  if (closes.some((value) => !validPositive(value))) return [];
  const fast = emaValues(closes, fastPeriod);
  const slow = emaValues(closes, slowPeriod);
  const offset = slowPeriod - fastPeriod;
  const macdValues = slow.map((value, index) => fast[index + offset] - value);
  const signalValues = emaValues(macdValues, signalPeriod);
  const signalOffset = signalPeriod - 1;
  return signalValues.map((signal, index) => {
    const macd = macdValues[index + signalOffset];
    return {
      time: candles[slowPeriod - 1 + index + signalOffset].time,
      macd,
      signal,
      histogram: macd - signal,
    };
  });
}

export function calculateVWAP(candles) {
  if (!Array.isArray(candles)) return [];
  const sessions = new Map();
  const points = [];
  for (const candle of candles) {
    const { time, high, low, close, volume } = candle || {};
    if (!Number.isFinite(time) || ![high, low, close].every(validPositive) ||
        high < low || volume === null || volume === undefined || !Number.isFinite(volume) || volume <= 0) continue;
    const day = new Date(time * 1000).toISOString().slice(0, 10);
    const typicalPrice = (high + low + close) / 3;
    const current = sessions.get(day) || { priceVolume: 0, volume: 0 };
    current.priceVolume += typicalPrice * volume;
    current.volume += volume;
    sessions.set(day, current);
    points.push({ time, value: current.priceVolume / current.volume });
  }
  return points;
}
