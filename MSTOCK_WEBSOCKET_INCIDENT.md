# m.Stock WebSocket Incident Findings

**Status:** Open — live WebSocket feed is not connected  
**Last evidence captured:** 13 November 2026  
**Scope:** m.Stock market-data WebSocket only. This is not an Operator/browser-agent issue.

## Executive summary

The m.Stock REST gateway endpoints tested successfully, but the m.Stock WebSocket connection repeatedly failed during the HTTP upgrade handshake with **502 Bad Gateway** from an AWS load balancer (\`awselb/2.0\`). The failure occurs before the client sends the application-level LOGIN or subscription messages. Therefore, the evidence currently points to a connection-establishment/upstream path problem, not a demonstrated login, token, subscription, or market-data parsing failure.

The user reports that Claude independently reached the same broad conclusion that the issue is isolated to the m.Stock live-feed connection. Claude's detailed test output was not available in this repository update, so no additional Claude-specific measurements are represented as verified facts here.

## Confirmed observations

| Area | Observation |
|---|---|
| WebSocket endpoint | \`wss://ws.mstock.trade\` |
| DNS destination | AWS load-balancer addresses in \`ap-south-1\` (Mumbai): \`13.200.68.179\`, \`15.206.54.73\` |
| Gateway host region | EC2 instance in \`ap-southeast-2\` (Sydney) |
| Gateway host public IP | \`54.153.201.74\` |
| Network/TLS | TCP 443 and TLS 1.3 connection succeeded; certificate validation succeeded |
| WebSocket handshake | Repeated HTTP \`502 Bad Gateway\`; response server identified as \`awselb/2.0\` |
| Application protocol | Handshake fails before LOGIN and subscription payloads are sent |
| Client | \`websocket-client\` 1.9.0; no proxy environment variables were present in the tested shell |
| Worker status (last captured) | \`connected:false\`, \`running:true\`, \`stale:true\`, \`reconnect_count:45\`, no cached instruments/ticks; token \`2885\`, full mode |
| REST gateway | Tested \`/quote\`, \`/index-quote\`, \`/gainers-losers\`, \`/instruments\`, and historical data endpoints returned HTTP 200 |

The WebSocket worker was configured with token \`2885\` in full mode. The worker's reported \`running:true\` state means its reconnect loop was active; it does **not** mean the upstream WebSocket was connected or delivering ticks.

## What the evidence does and does not establish

### Established

1. DNS resolution, outbound TCP connectivity, and TLS negotiation to the Mumbai load-balancer endpoint worked from the Sydney EC2 host.
2. The WebSocket upgrade handshake did not complete; the load balancer returned HTTP 502.
3. Because the failure precedes application-level LOGIN/subscription messages, changing the subscription payload or tick parser is not supported as the first remediation.
4. The tested REST paths were responding, so REST success must not be treated as proof that the WebSocket service is healthy.

### Not yet established — investigation required

- Whether the m.Stock WebSocket upstream/target was unhealthy or unavailable at the time.
- Whether the AWS load balancer had an upgrade, listener, target-group, routing, or health-check problem.
- Whether the connection was rejected based on source network/IP, geography, or a client-specific condition.
- Whether a direct test from an India-based network succeeds. The recorded network test was made from the Sydney EC2 host to the Mumbai endpoint; it is **not** an India-origin client test.
- Whether the same failure is reproducible from another independent network/client using the same documented endpoint and valid credentials.

The Sydney-to-Mumbai region difference is a useful diagnostic lead, not proof of the cause.

## Next diagnostic steps

1. Reproduce the handshake from an India-based network and record timestamp (IST), source network/provider, resolved IP, TLS result, HTTP status, response headers, and sanitized error text.
2. Run a controlled comparison from a second independent network/client. Keep endpoint, credentials, and WebSocket protocol constant; do not expose API keys, access tokens, TOTP values, or gateway secrets in logs.
3. Ask m.Stock to inspect the WebSocket service and AWS load-balancer/target-group health for the exact failure timestamps. Provide sanitized request metadata and response headers, never credentials.
4. Compare the India-origin and Sydney-origin results:
   - Both return 502: prioritize m.Stock upstream/load-balancer availability and routing.
   - India succeeds while Sydney fails: investigate source-network/geographic/IP policy or regional routing.
   - Both complete the handshake but later fail: only then investigate LOGIN, subscription, heartbeat, and message-format behavior.
5. After the handshake is restored, verify authentication, subscription acknowledgement, tick receipt, cache freshness, and reconnect behavior before declaring live streaming healthy.

## Operational safeguards

- Keep the existing REST gateway behavior unchanged.
- Do not rewrite the WebSocket URL, alter the application protocol, move the EC2 host, or repeatedly restart production services without evidence and approval.
- Do not change trading/order execution, broker integration, database state, or unrelated market pages as part of this incident.
- Keep credentials and tokens out of documentation, screenshots, shell history, and diagnostic output.
- Report REST health and WebSocket health separately.

## Current conclusion

**The m.Stock REST gateway is responding, while the m.Stock WebSocket upgrade path is failing with an AWS load-balancer HTTP 502 from the tested Sydney EC2 source. The root cause remains unconfirmed. An India-origin handshake test and m.Stock-side load-balancer/upstream evidence are the key missing checks.**
