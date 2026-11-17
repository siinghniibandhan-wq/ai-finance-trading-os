export function appendLivePricePoint(history, snapshot, limit = 60) {
  const timestamp = snapshot?.feed?.last_tick_at;
  const contracts = snapshot?.futures_contracts;
  if (!timestamp || !Array.isArray(contracts)) return history;

  const prices = Object.fromEntries(
    contracts
      .filter(item => item?.tradingsymbol && Number.isFinite(Number(item.price)))
      .map(item => [item.tradingsymbol, Number(item.price)])
  );
  if (Object.keys(prices).length === 0) return history;
  if (history.at(-1)?.timestamp === timestamp) return history;

  return [...history, { timestamp, prices }].slice(-Math.max(1, limit));
}
