export function buildOrderFlowWebSocketUrl(apiBaseUrl, symbol) {
  const url = new URL("/api/order-flow/stream", apiBaseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  if (symbol) url.searchParams.set("symbol", symbol);
  return url.toString();
}

export function buildOrderFlowWebSocketProtocols(accessToken) {
  const token = String(accessToken || "").trim();
  if (!token) throw new Error("A Financial OS access token is required.");
  return ["financial-os", `bearer.${token}`];
}
