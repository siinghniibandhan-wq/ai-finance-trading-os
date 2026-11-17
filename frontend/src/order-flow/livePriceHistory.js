export function appendLivePricePoint(history, snapshot, limit = 60) {
  const latestFeedTime = Date.parse(snapshot?.feed?.last_tick_at || "");
  const contracts = snapshot?.futures_contracts;
  if (
    snapshot?.feed?.status !== "fresh"
    || !Number.isFinite(latestFeedTime)
    || !Array.isArray(contracts)
  ) return history;

  let next = history.slice();
  let changed = false;
  for (const item of contracts) {
    const timestamp = item?.exchange_timestamp;
    const time = Date.parse(timestamp || "");
    const symbol = item?.tradingsymbol;
    const price = Number(item?.price);
    if (!symbol || !Number.isFinite(time) || !Number.isFinite(price) || price <= 0) continue;
    if (latestFeedTime - time > 15000) continue;

    const previous = [...next].reverse().find(point => (
      Object.prototype.hasOwnProperty.call(point.prices, symbol)
    ));
    if (previous && time <= Date.parse(previous.timestamp)) continue;

    const sameTimeIndex = next.findIndex(point => point.timestamp === timestamp);
    if (sameTimeIndex >= 0) {
      if (next[sameTimeIndex].prices[symbol] !== price) {
        next[sameTimeIndex] = {
          ...next[sameTimeIndex],
          prices: { ...next[sameTimeIndex].prices, [symbol]: price },
        };
        changed = true;
      }
    } else {
      next.push({ timestamp, prices: { [symbol]: price } });
      changed = true;
    }
  }

  if (!changed) return history;
  next.sort((left, right) => Date.parse(left.timestamp) - Date.parse(right.timestamp));
  return next.slice(-Math.max(1, limit));
}
