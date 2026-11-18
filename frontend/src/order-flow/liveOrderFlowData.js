const finiteNumber = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const cleanSymbol = (value) => String(value || "").trim().toUpperCase();

export function buildLiveOrderFlow(snapshot, selectedSymbol = "") {
  const selected = cleanSymbol(selectedSymbol);
  const usable = snapshot?.status === "success" && snapshot?.feed?.status === "fresh";
  if (!usable) {
    return {
      isLive: false,
      feed: snapshot?.feed || { status: "disconnected", last_tick_at: null, age_seconds: null },
      stream: snapshot?.stream || {},
      futures: [],
      options: [],
      optionOiByStrike: [],
      underlyings: [],
      asOf: null,
      coverage: snapshot?.coverage || {},
    };
  }

  const matches = (row) => !selected || cleanSymbol(row?.symbol) === selected;
  const futures = (Array.isArray(snapshot.futures_contracts) ? snapshot.futures_contracts : [])
    .filter(matches)
    .map((row) => {
      const totalBuyQuantity = finiteNumber(row.total_buy_quantity);
      const totalSellQuantity = finiteNumber(row.total_sell_quantity);
      const totalDepthQuantity = (totalBuyQuantity || 0) + (totalSellQuantity || 0);
      return {
      symbol: cleanSymbol(row.symbol),
      contract: String(row.tradingsymbol || ""),
      exchange: String(row.exchange || ""),
      expiry: String(row.expiry || ""),
      price: finiteNumber(row.price),
      volume: finiteNumber(row.volume),
      oi: finiteNumber(row.oi),
      changePct: finiteNumber(row.change_pct),
      ohlc: row.ohlc && typeof row.ohlc === "object" ? {
        open: finiteNumber(row.ohlc.open),
        high: finiteNumber(row.ohlc.high),
        low: finiteNumber(row.ohlc.low),
        close: finiteNumber(row.ohlc.close),
      } : null,
      openInterestHigh: finiteNumber(row.open_interest_high),
      openInterestLow: finiteNumber(row.open_interest_low),
      averageTradedPrice: finiteNumber(row.average_traded_price),
      lastTradedQuantity: finiteNumber(row.last_traded_quantity),
      totalBuyQuantity,
      totalSellQuantity,
      buySellBalancePct: totalDepthQuantity > 0
        ? ((totalBuyQuantity - totalSellQuantity) / totalDepthQuantity) * 100
        : null,
      receivedAt: row.received_at || null,
      exchangeTimestamp: row.exchange_timestamp || null,
    };
    })
    .filter((row) => row.symbol && row.price !== null && row.price > 0)
    .sort((a, b) => a.symbol.localeCompare(b.symbol) || a.expiry.localeCompare(b.expiry));

  const options = (Array.isArray(snapshot.option_contracts) ? snapshot.option_contracts : [])
    .filter(matches)
    .map((row) => ({
      symbol: cleanSymbol(row.symbol),
      contract: String(row.tradingsymbol || ""),
      exchange: String(row.exchange || ""),
      expiry: String(row.expiry || ""),
      strike: finiteNumber(row.strike),
      optionType: String(row.option_type || "").toUpperCase(),
      price: finiteNumber(row.price),
      volume: finiteNumber(row.volume),
      oi: finiteNumber(row.oi),
      changePct: finiteNumber(row.change_pct),
      lastTradedQuantity: finiteNumber(row.last_traded_quantity),
      receivedAt: row.received_at || null,
      exchangeTimestamp: row.exchange_timestamp || null,
    }))
    .filter((row) => row.symbol && row.strike !== null && row.strike > 0 &&
      ["CE", "PE"].includes(row.optionType) && row.oi !== null)
    .sort((a, b) => a.symbol.localeCompare(b.symbol) ||
      a.expiry.localeCompare(b.expiry) || a.strike - b.strike ||
      a.optionType.localeCompare(b.optionType));

  const optionOiByStrike = (Array.isArray(snapshot.option_oi_by_strike) ? snapshot.option_oi_by_strike : [])
    .map((row) => ({
      symbol: cleanSymbol(row?.symbol),
      expiry: String(row?.expiry || ""),
      strike: finiteNumber(row?.strike),
      callOi: finiteNumber(row?.ce_oi),
      putOi: finiteNumber(row?.pe_oi),
    }))
    .filter((row) => row.symbol && row.expiry && row.strike !== null && row.strike > 0 &&
      (row.callOi !== null || row.putOi !== null))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) ||
      a.expiry.localeCompare(b.expiry) || a.strike - b.strike);

  const underlyings = [...new Set([
    ...futures.map((row) => row.symbol),
    ...options.map((row) => row.symbol),
  ])].sort();

  return {
    isLive: true,
    feed: snapshot.feed,
    stream: snapshot.stream || {},
    futures,
    options,
    optionOiByStrike,
    underlyings,
    asOf: snapshot.as_of || snapshot.feed?.last_tick_at || null,
    coverage: snapshot.coverage || {},
  };
}

export function formatMarketNumber(value) {
  const number = finiteNumber(value);
  return number === null ? "—" : new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(number);
}

export function formatMarketTimestamp(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "Asia/Kolkata",
  });
}

export function formatMarketPercent(value) {
  const number = finiteNumber(value);
  if (number === null) return "—";
  return `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
}


export function appendLivePriceHistory(history, snapshot, maxPoints = 1800) {
  if (snapshot?.status !== "success" || snapshot?.feed?.status !== "fresh") return history;
  const incoming = (Array.isArray(snapshot.futures_contracts) ? snapshot.futures_contracts : [])
    .map((row) => ({
      symbol: cleanSymbol(row?.symbol),
      contract: String(row?.tradingsymbol || ""),
      price: finiteNumber(row?.price),
      timestamp: row?.exchange_timestamp || row?.received_at || snapshot.as_of || null,
    }))
    .filter((row) => row.symbol && row.contract && row.price !== null && row.price > 0 && row.timestamp &&
      !Number.isNaN(new Date(row.timestamp).getTime()));
  if (!incoming.length) return history;
  const next = Array.isArray(history) ? history.slice() : [];
  for (const point of incoming) {
    const key = point.symbol + "|" + point.contract;
    let lastIndex = -1;
    for (let index = next.length - 1; index >= 0; index -= 1) {
      if (next[index].symbol + "|" + next[index].contract === key) {
        lastIndex = index;
        break;
      }
    }
    if (lastIndex >= 0 && next[lastIndex].timestamp === point.timestamp) {
      next[lastIndex] = point;
    } else {
      next.push(point);
    }
  }
  const grouped = new Map();
  for (const point of next) {
    const key = point.symbol + "|" + point.contract;
    const group = grouped.get(key) || [];
    group.push(point);
    grouped.set(key, group);
  }
  const cap = Math.max(1, Number(maxPoints) || 1800);
  return [...grouped.values()].flatMap((group) => group.slice(-cap));
}
