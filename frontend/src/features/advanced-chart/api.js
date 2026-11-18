import { API_BASE_URL, apiFetch } from "../../api";
import { buildInstrumentSearchParams } from "./model";

async function readResponse(response, label) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload?.detail === "string"
      ? payload.detail
      : payload?.detail?.message || `${label} returned HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

export async function searchChartInstruments(query, exchange = "ALL") {
  const params = buildInstrumentSearchParams(query, exchange);
  const response = await apiFetch(`${API_BASE_URL}/api/market-search/?${params}`, {
    cache: "no-store",
  });
  const payload = await readResponse(response, "Instrument search");
  return Array.isArray(payload?.results) ? payload.results : [];
}

export async function loadChartHistory({ symbol, exchange, interval, from, to }) {
  const params = new URLSearchParams({
    symbol,
    exchange,
    interval,
    from,
    to,
  });
  const response = await apiFetch(`${API_BASE_URL}/api/market-charts/?${params}`, {
    cache: "no-store",
  });
  return readResponse(response, "Historical chart data");
}

export async function loadLatestQuote({ symbol, exchange }) {
  const params = new URLSearchParams({ symbol, exchange });
  const response = await apiFetch(`${API_BASE_URL}/api/market-quote/?${params}`, {
    cache: "no-store",
  });
  return readResponse(response, "Latest quote");
}

export async function loadMarketMovers(type = "losers", limit = 100) {
  const params = new URLSearchParams({ type, limit: String(limit) });
  const response = await apiFetch(`${API_BASE_URL}/api/market-movers/?${params}`, {
    cache: "no-store",
  });
  return readResponse(response, "Market movers");
}

export async function loadMarketOverview() {
  const response = await apiFetch(`${API_BASE_URL}/api/market-overview/`, {
    cache: "no-store",
  });
  return readResponse(response, "Market overview");
}
