import { API_BASE_URL, apiFetch } from "../../api";

async function readOptionsResponse(response, label) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload?.detail === "string"
      ? payload.detail
      : payload?.detail?.message || `${label} returned HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

export async function loadOptionsMaster(exchange = "NSE") {
  const params = new URLSearchParams({ exchange });
  const response = await apiFetch(`${API_BASE_URL}/api/options-hub/master?${params}`, {
    cache: "no-store",
  });
  return readOptionsResponse(response, "Options master");
}

export async function loadOptionsChain({ exchange = "NSE", underlying, expiry }) {
  const params = new URLSearchParams({ exchange, underlying, expiry });
  const response = await apiFetch(`${API_BASE_URL}/api/options-hub/chain?${params}`, {
    cache: "no-store",
  });
  return readOptionsResponse(response, "Options chain");
}
