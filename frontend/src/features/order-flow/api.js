import { API_BASE_URL, apiFetch } from "../../api";

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

export async function loadMarketFlowSectorMovers(sectorKey) {
  const response = await apiFetch(
    `${API_BASE_URL}/api/market-flow/sectors/${encodeURIComponent(sectorKey)}`,
    { cache: "no-store" },
  );
  return readResponse(response, "Sector market movers");
}
