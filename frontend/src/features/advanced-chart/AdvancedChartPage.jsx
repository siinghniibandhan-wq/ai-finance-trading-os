import React, { useEffect, useMemo, useRef, useState } from "react";
import { CandlestickSeries, HistogramSeries, LineSeries, createChart } from "lightweight-charts";
import { loadChartHistory, loadLatestQuote, searchChartInstruments } from "./api";
import MarketFlowBoard from "./MarketFlowBoard";
import { calculateEMA, calculateSMA, formatChartTime, getChartDimensions, getDefaultChartRange, normalizeCandles, normalizeQuotePrice } from "./model";
import { calculateBollingerBands, calculateVWAP } from "./indicators";
import "./advanced-chart.css";

const INTERVALS = [
  { value: "minute", label: "1m" },
  { value: "3minute", label: "3m" },
  { value: "5minute", label: "5m" },
  { value: "10minute", label: "10m" },
  { value: "15minute", label: "15m" },
  { value: "30minute", label: "30m" },
  { value: "60minute", label: "1h" },
  { value: "day", label: "1D" },
];

const money = (value) => {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount)
    : "—";
};

export default function AdvancedChartPage() {
  const [activeView, setActiveView] = useState("flow");
  const [query, setQuery] = useState("");
  const [exchangeFilter, setExchangeFilter] = useState("ALL");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [instrument, setInstrument] = useState(null);
  const [interval, setInterval] = useState("5minute");
  const [range, setRange] = useState(() => getDefaultChartRange());
  const [candles, setCandles] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [quote, setQuote] = useState(null);
  const [quoteError, setQuoteError] = useState("");
  const [quoteBusy, setQuoteBusy] = useState(false);
  const [showSma, setShowSma] = useState(false);
  const [showEma, setShowEma] = useState(false);
  const [showVwap, setShowVwap] = useState(false);
  const [showBollinger, setShowBollinger] = useState(false);
  const [hoveredCandle, setHoveredCandle] = useState(null);
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const smaSeriesRef = useRef(null);
  const emaSeriesRef = useRef(null);
  const vwapSeriesRef = useRef(null);
  const bollingerUpperRef = useRef(null);
  const bollingerMiddleRef = useRef(null);
  const bollingerLowerRef = useRef(null);
  const lastPriceLineRef = useRef(null);

  const selectedLabel = useMemo(() => {
    if (!instrument) return "Select an instrument";
    return `${instrument.symbol} · ${instrument.exchange}`;
  }, [instrument]);

  const runSearch = async (event) => {
    event.preventDefault();
    if (!query.trim()) {
      setSearchError("Enter a company name or trading symbol.");
      setResults([]);
      return;
    }
    setSearching(true);
    setSearchError("");
    setResults([]);
    try {
      const matches = await searchChartInstruments(query, exchangeFilter);
      setResults(matches);
      if (!matches.length) setSearchError("No NSE/BSE cash instruments matched that search.");
    } catch (error) {
      setSearchError(error?.message || "Instrument search failed.");
    } finally {
      setSearching(false);
    }
  };

  const selectInstrument = (item) => {
    if (!item?.symbol || !["NSE", "BSE"].includes(String(item.exchange).toUpperCase())) return;
    setInstrument({
      symbol: String(item.symbol).trim().toUpperCase(),
      exchange: String(item.exchange).trim().toUpperCase(),
      name: item.name || item.symbol,
    });
    setResults([]);
    setSearchError("");
    setQuote(null);
    setQuoteError("");
    setQuoteBusy(false);
  };

  useEffect(() => {
    if (!instrument) {
      setCandles([]);
      setHistoryLoading(false);
      setHistoryError("");
      return undefined;
    }
    let current = true;
    setCandles([]);
    setHistoryLoading(true);
    setHistoryError("");
    loadChartHistory({
      symbol: instrument.symbol,
      exchange: instrument.exchange,
      interval,
      from: range.from,
      to: range.to,
    }).then((payload) => {
      if (!current) return;
      const normalized = normalizeCandles(payload?.data);
      setCandles(normalized);
      if (!normalized.length) {
        setHistoryError("The provider returned no valid OHLCV candles for this instrument and date range.");
      }
    }).catch((error) => {
      if (!current) return;
      setCandles([]);
      setHistoryError(error?.message || "Historical chart data could not be loaded.");
    }).finally(() => {
      if (current) setHistoryLoading(false);
    });
    return () => { current = false; };
  }, [instrument, interval, range.from, range.to]);

  useEffect(() => {
    if (!instrument) return undefined;
    let current = true;
    let inFlight = false;
    const refreshQuote = async () => {
      if (inFlight || document.visibilityState !== "visible") return;
      inFlight = true;
      setQuoteBusy(true);
      try {
        const payload = await loadLatestQuote(instrument);
        if (current) {
          setQuote(payload);
          setQuoteError("");
        }
      } catch (error) {
        if (current) setQuoteError(error?.message || "Latest quote is unavailable.");
      } finally {
        inFlight = false;
        if (current) setQuoteBusy(false);
      }
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") refreshQuote();
    };
    refreshQuote();
    const timer = window.setInterval(refreshQuote, 10000);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      current = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [instrument]);

  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container) return undefined;

    const chart = createChart(container, {
      ...getChartDimensions(container.clientWidth, container.clientHeight),
      layout: {
        background: { color: "transparent" },
        attributionLogo: true,
        textColor: getComputedStyle(container).getPropertyValue("--finos-muted").trim() || "#9ca3af",
        fontFamily: "Inter, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: getComputedStyle(container).getPropertyValue("--finos-border").trim() || "#30343d" },
        horzLines: { color: getComputedStyle(container).getPropertyValue("--finos-border").trim() || "#30343d" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: getComputedStyle(container).getPropertyValue("--finos-border").trim() || "#30343d" },
      timeScale: {
        borderColor: getComputedStyle(container).getPropertyValue("--finos-border").trim() || "#30343d",
        timeVisible: true,
        secondsVisible: false,
      },
      localization: {
        priceFormatter: (price) => money(price),
      },
    });
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#16a36a",
      downColor: "#e05260",
      borderVisible: false,
      wickUpColor: "#16a36a",
      wickDownColor: "#e05260",
      priceLineVisible: true,
    });
    const smaSeries = chart.addSeries(LineSeries, {
      color: "#e6a23c",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: showSma,
      title: "SMA 20",
    });
    const emaSeries = chart.addSeries(LineSeries, {
      color: "#4b9fe8",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: showEma,
      title: "EMA 20",
    });
    const vwapSeries = chart.addSeries(LineSeries, { color: "#b58cff", lineWidth: 2, priceLineVisible: false, lastValueVisible: false, visible: showVwap, title: "VWAP" });
    const bollingerUpper = chart.addSeries(LineSeries, { color: "rgba(91,156,245,0.8)", lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, visible: showBollinger, title: "BB Upper" });
    const bollingerMiddle = chart.addSeries(LineSeries, { color: "rgba(91,156,245,0.55)", lineWidth: 1, priceLineVisible: false, lastValueVisible: false, visible: showBollinger, title: "BB Middle" });
    const bollingerLower = chart.addSeries(LineSeries, { color: "rgba(91,156,245,0.8)", lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, visible: showBollinger, title: "BB Lower" });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "",
      lastValueVisible: false,
      priceLineVisible: false,
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });
    const onCrosshairMove = (param) => {
      const candle = param?.seriesData?.get(candleSeries);
      if (!candle) {
        setHoveredCandle(null);
        return;
      }
      const volume = param.seriesData.get(volumeSeries);
      setHoveredCandle({ ...candle, volume: volume?.value ?? null });
    };
    chart.subscribeCrosshairMove(onCrosshairMove);
    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    smaSeriesRef.current = smaSeries;
    emaSeriesRef.current = emaSeries;
    vwapSeriesRef.current = vwapSeries;
    bollingerUpperRef.current = bollingerUpper;
    bollingerMiddleRef.current = bollingerMiddle;
    bollingerLowerRef.current = bollingerLower;

    const resize = () => {
      chart.applyOptions(getChartDimensions(container.clientWidth, container.clientHeight));
    };
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
    observer?.observe(container);
    window.addEventListener("resize", resize);

    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", resize);
      chart.unsubscribeCrosshairMove(onCrosshairMove);
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      smaSeriesRef.current = null;
      emaSeriesRef.current = null;
      vwapSeriesRef.current = null;
      bollingerUpperRef.current = null;
      bollingerMiddleRef.current = null;
      bollingerLowerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || !smaSeriesRef.current || !emaSeriesRef.current) return;
    setHoveredCandle(null);
    candleSeriesRef.current.setData(candles);
    volumeSeriesRef.current.setData(candles
      .filter((candle) => Number.isFinite(candle.volume) && candle.volume >= 0)
      .map((candle) => ({
        time: candle.time,
        value: candle.volume,
        color: candle.close >= candle.open ? "rgba(22,163,106,0.48)" : "rgba(224,82,96,0.48)",
      })));
    smaSeriesRef.current.setData(calculateSMA(candles, 20));
    emaSeriesRef.current.setData(calculateEMA(candles, 20));
    vwapSeriesRef.current?.setData(calculateVWAP(candles));
    const bands = calculateBollingerBands(candles, 20, 2);
    bollingerUpperRef.current?.setData(bands.map(({ time, upper }) => ({ time, value: upper })));
    bollingerMiddleRef.current?.setData(bands.map(({ time, middle }) => ({ time, value: middle })));
    bollingerLowerRef.current?.setData(bands.map(({ time, lower }) => ({ time, value: lower })));
    if (candles.length) chartRef.current?.timeScale().fitContent();
  }, [candles]);

  useEffect(() => {
    smaSeriesRef.current?.applyOptions({ visible: showSma });
    emaSeriesRef.current?.applyOptions({ visible: showEma });
    vwapSeriesRef.current?.applyOptions({ visible: showVwap });
    bollingerUpperRef.current?.applyOptions({ visible: showBollinger });
    bollingerMiddleRef.current?.applyOptions({ visible: showBollinger });
    bollingerLowerRef.current?.applyOptions({ visible: showBollinger });
  }, [showSma, showEma, showVwap, showBollinger]);

  const lastPrice = quote?.quote?.last_price;
  const normalizedLastPrice = normalizeQuotePrice(quote);

  // The quote endpoint is polled every 10 seconds. Reflect only its verified
  // last-traded price as a chart price line; do not fabricate or mutate an
  // OHLC candle from a quote snapshot.
  useEffect(() => {
    const series = candleSeriesRef.current;
    if (!series) return;
    if (lastPriceLineRef.current) {
      series.removePriceLine(lastPriceLineRef.current);
      lastPriceLineRef.current = null;
    }
    if (normalizedLastPrice !== null) {
      lastPriceLineRef.current = series.createPriceLine({
        price: normalizedLastPrice,
        color: "#e6a23c",
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: true,
        title: "LTP",
      });
    }
  }, [normalizedLastPrice]);
  const retrievalTime = quote?.retrieved_at
    ? new Date(quote.retrieved_at).toLocaleString("en-IN")
    : "Not available";
  const hasGatewayCacheAge = quote?.cache_age_seconds !== null &&
    quote?.cache_age_seconds !== undefined &&
    Number.isFinite(Number(quote.cache_age_seconds));
  const gatewayCacheAge = hasGatewayCacheAge
    ? `${Number(quote.cache_age_seconds).toFixed(1)}s`
    : "Not reported";
  const readoutCandle = hoveredCandle || candles[candles.length - 1] || null;

  return (
    <main className="advanced-chart-page">
      <header className="advanced-chart-header">
        <div>
          <div className="advanced-chart-eyebrow">MARKETS / ANALYSIS</div>
          <h1>Advanced Chart</h1>
          <p>Interactive m.Stock OHLCV charting. Market values are loaded from the connected provider.</p>
        </div>
        <div className="advanced-chart-source">SOURCE <strong>m.Stock · Financial OS API</strong></div>
      </header>

      <nav className="advanced-chart-view-tabs" aria-label="Advanced Chart views">
        <button type="button" className={activeView === "flow" ? "is-active" : ""} aria-pressed={activeView === "flow"} onClick={() => setActiveView("flow")}>Market Flow</button>
        <button type="button" className={activeView === "chart" ? "is-active" : ""} aria-pressed={activeView === "chart"} onClick={() => setActiveView("chart")}>Advanced Chart</button>
      </nav>
      {activeView === "flow" ? (
        <MarketFlowBoard onSelectInstrument={(item) => { selectInstrument(item); setActiveView("chart"); }} />
      ) : (
        <>
      <section className="advanced-chart-toolbar" aria-label="Chart controls">
        <form className="advanced-chart-search" onSubmit={runSearch}>
          <label htmlFor="advanced-chart-symbol">Instrument</label>
          <div className="advanced-chart-search-row">
            <input id="advanced-chart-symbol" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search symbol or company" autoComplete="off" />
            <button type="submit" disabled={searching}>{searching ? "Searching…" : "Search"}</button>
          </div>
        </form>
        <label className="advanced-chart-control">
          <span>Exchange filter</span>
          <select value={exchangeFilter} onChange={(event) => setExchangeFilter(event.target.value)}>
            <option value="ALL">NSE + BSE</option>
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
        </label>
        <div className="advanced-chart-selection">
          <span>SELECTED</span>
          <strong>{selectedLabel}</strong>
          {instrument?.name && <small>{instrument.name}</small>}
        </div>
        <label className="advanced-chart-control">
          <span>Interval</span>
          <select value={interval} onChange={(event) => setInterval(event.target.value)}>
            {INTERVALS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
        <label className="advanced-chart-control">
          <span>From</span>
          <input type="date" value={range.from} max={range.to} onChange={(event) => setRange((old) => ({ ...old, from: event.target.value }))} />
        </label>
        <label className="advanced-chart-control">
          <span>To</span>
          <input type="date" value={range.to} min={range.from} max={getDefaultChartRange(new Date(), 0).to} onChange={(event) => setRange((old) => ({ ...old, to: event.target.value }))} />
        </label>
      </section>

      {searchError && <div className="advanced-chart-message" role="status">{searchError}</div>}
      {results.length > 0 && (
        <section className="advanced-chart-results" aria-label="Instrument search results">
          {results.map((item, index) => (
            <button type="button" key={`${item.exchange}-${item.symbol}-${index}`} onClick={() => selectInstrument(item)}>
              <strong>{item.symbol}</strong><span>{item.name}</span><small>{item.exchange} · {item.series || "Cash"}</small>
            </button>
          ))}
        </section>
      )}

      <section className="advanced-chart-market-strip">
        <div><span>LAST TRADED PRICE</span><strong>{lastPrice === null || lastPrice === undefined ? "—" : `₹${money(lastPrice)}`}</strong></div>
        <div><span>QUOTE SOURCE</span><strong>{quote?.source?.provider || "Awaiting quote"}</strong></div>
        <div><span>QUOTE RETRIEVED</span><strong>{retrievalTime}</strong></div>
        <div><span>GATEWAY CACHE AGE</span><strong>{gatewayCacheAge}</strong></div>
        <div><span>QUOTE MODE</span><strong>{quote ? "10s snapshot polling" : "Not connected"}</strong></div>
      </section>
      {quoteError && <div className="advanced-chart-warning" role="status">{quoteError}{quote ? " · Showing the last successful quote." : ""}</div>}

      <section className="advanced-chart-panel">
        <div className="advanced-chart-panel-heading">
          <div>
            <h2>{instrument ? instrument.symbol : "Price chart"}</h2>
            <span>{instrument ? `${instrument.exchange} · ${INTERVALS.find((item) => item.value === interval)?.label} · OHLCV` : "Search and select an instrument to load provider candles"}</span>
          </div>
          <div className="advanced-chart-panel-actions">
            <div className="advanced-chart-overlays" aria-label="Technical overlays">
              <span>OVERLAYS</span>
              <label><input type="checkbox" checked={showSma} disabled={!candles.length} onChange={(event) => setShowSma(event.target.checked)} /> SMA 20</label>
              <label><input type="checkbox" checked={showEma} disabled={!candles.length} onChange={(event) => setShowEma(event.target.checked)} /> EMA 20</label>
              <label><input type="checkbox" checked={showVwap} disabled={!candles.some((candle) => Number.isFinite(candle.volume) && candle.volume > 0)} onChange={(event) => setShowVwap(event.target.checked)} /> VWAP</label>
              <label><input type="checkbox" checked={showBollinger} disabled={candles.length < 20} onChange={(event) => setShowBollinger(event.target.checked)} /> Bollinger 20,2</label>
            </div>
            <div className="advanced-chart-status">
            {historyLoading ? "Loading historical data…" : candles.length ? `${candles.length.toLocaleString("en-IN")} candles loaded` : "No chart data"}
            {quoteBusy && <small>Refreshing quote</small>}
            </div>
          </div>
        </div>
        {historyError && <div className="advanced-chart-warning" role="status">{historyError}</div>}
        {(showSma || showEma || showBollinger) && candles.length < 20 && <div className="advanced-chart-message" role="status">20-period overlays appear after at least 20 valid candles are available.</div>
        {showVwap && !candles.some((candle) => Number.isFinite(candle.volume) && candle.volume > 0) && <div className="advanced-chart-message" role="status">VWAP requires provider-supplied candle volume.</div>}}
        <div className="advanced-chart-ohlcv" aria-label="Selected candle OHLCV" aria-live="polite">
          <span className="advanced-chart-ohlcv-time">{readoutCandle ? formatChartTime(readoutCandle.time) : "—"}</span>
          <span>O <strong>{readoutCandle ? money(readoutCandle.open) : "—"}</strong></span>
          <span>H <strong>{readoutCandle ? money(readoutCandle.high) : "—"}</strong></span>
          <span>L <strong>{readoutCandle ? money(readoutCandle.low) : "—"}</strong></span>
          <span>C <strong>{readoutCandle ? money(readoutCandle.close) : "—"}</strong></span>
          <span>V <strong>{readoutCandle?.volume === null || readoutCandle?.volume === undefined ? "—" : Number(readoutCandle.volume).toLocaleString("en-IN")}</strong></span>
        </div>
        <div className="advanced-chart-canvas" ref={chartContainerRef} aria-label="Interactive candlestick and volume chart" />
        <div className="advanced-chart-footnote">
          Historical candles: m.Stock provider data. The LTP line refreshes from authenticated REST quote snapshots every 10 seconds; quote snapshots do not rewrite OHLC candles and are not a continuous WebSocket tick stream. Quote retrieval time is not an exchange timestamp. TradingView Lightweight Charts™ Copyright (c) 2025 TradingView, Inc. · <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">TradingView</a>.
        </div>
      </section>
        </>
      )}
    </main>
  );
}
