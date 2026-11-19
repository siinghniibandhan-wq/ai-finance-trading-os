import { API_BASE_URL, apiFetch, friendlyErrorMessage } from "../../api";

async function request(path) {
  const response = await apiFetch(new URL(path, API_BASE_URL));
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(friendlyErrorMessage(response.status, payload));
  }
  if (payload?.status !== "success") {
    throw new Error(payload?.detail || payload?.message || "Options data is unavailable.");
  }
  return payload;
}

export function loadOptionChainMaster(exchange = "NSE") {
  return request(`/api/options-chain/master?exchange=${encodeURIComponent(exchange)}`);
}

export function loadOptionChain({ exchange = "NSE", expiry, token }) {
  const query = new URLSearchParams({
    exchange,
    expiry: String(expiry),
    token: String(token),
  });
  return request(`/api/options-chain/?${query.toString()}`);
}
