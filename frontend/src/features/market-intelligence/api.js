import { API_BASE_URL, apiFetch } from "../../api.js";
export async function loadCorporateActions({ symbol, exchange }) {
  const params = new URLSearchParams({ symbol, exchange });
  const response = await apiFetch(`${API_BASE_URL}/api/corporate-actions/?${params}`, { cache: "no-store" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : payload?.detail?.message || `Corporate actions returned HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}
