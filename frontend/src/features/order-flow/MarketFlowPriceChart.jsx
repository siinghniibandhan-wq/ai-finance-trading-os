import React, { useEffect, useRef, useState } from "react";
import { CandlestickSeries, HistogramSeries, createChart } from "lightweight-charts";
import { loadChartHistory } from "../advanced-chart/api.js";
import { normalizeMarketFlowCandles } from "./orderFlowModel.js";

const INTERVALS = [
  { value: "5minute", label: "5m" },
  { value: "15minute", label: "15m" },
  { value: "60minute", label: "1h" },
  { value: "day", label: "1D" },
];
const dateString = date => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return year + "-" + month + "-" + day;
};
const money = value => Number(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function MarketFlowPriceChart({ instrument }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const [interval, setInterval] = useState("5minute");
  const [candles, setCandles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    if (!instrument?.symbol || !instrument?.exchange) {
      setCandles([]);
      setError("");
      return undefined;
    }
    let active = true;
    const to = new Date();
    const from = new Date(to);
    from.setDate(from.getDate() - (interval === "day" ? 180 : 7));
    setLoading(true);
    setError("");
    loadChartHistory({
      symbol: instrument.symbol,
      exchange: instrument.exchange,
      interval,
      from: dateString(from),
      to: dateString(to),
    }).then(payload => {
      if (!active) return;
      const next = normalizeMarketFlowCandles(payload?.data);
      setCandles(next);
      if (!next.length) setError("No valid historical candles were returned for this instrument and interval.");
    }).catch(requestError => {
      if (active) {
        setCandles([]);
        setError(requestError?.message || "Historical price data is unavailable.");
      }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [instrument?.symbol, instrument?.exchange, interval]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;
    const chart = createChart(container, {
      width: Math.max(320, container.clientWidth),
      height: 360,
      layout: { background: { color: "transparent" }, textColor: "#94a6b3", fontFamily: "Inter, system-ui, sans-serif" },
      grid: { vertLines: { color: "#1d2b35" }, horzLines: { color: "#1d2b35" } },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#263743" },
      timeScale: { borderColor: "#263743", timeVisible: true, secondsVisible: false },
      localization: { priceFormatter: money },
    });
    const candlesSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#39d49c", downColor: "#f07883", borderVisible: false,
      wickUpColor: "#39d49c", wickDownColor: "#f07883",
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" }, priceScaleId: "", lastValueVisible: false, priceLineVisible: false,
    });
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    chart.subscribeCrosshairMove(param => {
      const candle = param?.seriesData?.get(candlesSeries);
      setHovered(candle ? { ...candle, time: param.time } : null);
    });
    chartRef.current = chart;
    candleSeriesRef.current = candlesSeries;
    volumeSeriesRef.current = volumeSeries;
    const resize = () => chart.applyOptions({ width: Math.max(320, container.clientWidth) });
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
    observer?.observe(container);
    return () => {
      observer?.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;
    candleSeriesRef.current.setData(candles);
    volumeSeriesRef.current.setData(candles.filter(row => row.volume !== null).map(row => ({
      time: row.time,
      value: row.volume,
      color: row.close >= row.open ? "rgba(57,212,156,.38)" : "rgba(240,120,131,.38)",
    })));
    if (candles.length) chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return <section className="mfb-section mfb-history-chart" aria-label="Historical instrument price chart">
    <div className="mfb-section-head">
      <div><small>05 / PRICE & VOLUME HISTORY</small><h2>{instrument ? instrument.symbol + " · Historical OHLCV" : "Historical OHLCV"}</h2>
        <p>Broker-supplied candles from the existing Market Charts engine. Historical data is separate from the shared live movers snapshot.</p></div>
      <div className="mfb-chart-intervals" aria-label="Historical chart interval">
        {INTERVALS.map(item => <button key={item.value} type="button" className={interval === item.value ? "active" : ""} onClick={() => setInterval(item.value)}>{item.label}</button>)}
      </div>
    </div>
    {instrument ? <div className="mfb-chart-readout">
      <span>{loading ? "Loading candles…" : candles.length + " candles"}</span>
      {hovered && <><span>O {money(hovered.open)}</span><span>H {money(hovered.high)}</span><span>L {money(hovered.low)}</span><span>C {money(hovered.close)}</span><span>V {hovered.volume == null ? "—" : Number(hovered.volume).toLocaleString("en-IN")}</span></>}
    </div> : <p className="mfb-chart-empty">Select an instrument from the bullish or bearish flow to load its historical chart.</p>}
    {error && <p className="mfb-alert" role="status">{error}</p>}
    <div className="mfb-history-canvas" ref={containerRef} />
  </section>;
}
