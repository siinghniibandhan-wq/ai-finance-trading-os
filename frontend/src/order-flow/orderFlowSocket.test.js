import test from "node:test";
import assert from "node:assert/strict";
import {
  buildOrderFlowWebSocketProtocols,
  buildOrderFlowWebSocketUrl,
} from "./orderFlowSocket.js";

test("builds a secure WSS URL for the configured production API origin", () => {
  const url = new URL(buildOrderFlowWebSocketUrl("https://wealthmanager.example", "NIFTY"));
  assert.equal(url.protocol, "wss:");
  assert.equal(url.pathname, "/api/order-flow/stream");
  assert.equal(url.searchParams.get("symbol"), "NIFTY");
});

test("builds a local WS URL and omits an empty underlying filter", () => {
  const url = new URL(buildOrderFlowWebSocketUrl("http://127.0.0.1:8000", ""));
  assert.equal(url.protocol, "ws:");
  assert.equal(url.searchParams.has("symbol"), false);
});

test("sends the existing Bearer token in the WebSocket subprotocol, not the URL", () => {
  const protocols = buildOrderFlowWebSocketProtocols("header.payload.signature");
  assert.deepEqual(protocols, ["financial-os", "bearer.header.payload.signature"]);
  assert.throws(() => buildOrderFlowWebSocketProtocols(""), /access token is required/);
});
