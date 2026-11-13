"""Opt-in m.Stock Type A WebSocket runtime.

Credentials are read only from backend environment configuration. The stream is
read-only and remains disabled unless explicitly enabled with valid credentials
and instrument tokens. No broker order APIs are used.
"""
from __future__ import annotations

import os
from urllib.parse import urlencode

from app.services.mstock_stream_worker import MarketStreamWorker

DEFAULT_MSTOCK_STREAM_URL = "wss://ws.mstock.trade"


def _parse_tokens(raw: str) -> list[int]:
    tokens: list[int] = []
    for part in raw.split(","):
        value = part.strip()
        if not value:
            continue
        if not value.isdigit() or int(value) <= 0:
            raise ValueError("MSTOCK_STREAM_INSTRUMENT_TOKENS must be comma-separated positive integers.")
        tokens.append(int(value))
    return list(dict.fromkeys(tokens))


def get_stream_config(environ=None) -> dict:
    env = os.environ if environ is None else environ
    enabled = str(env.get("MSTOCK_STREAM_ENABLED", "")).strip().lower() in {"1", "true", "yes"}
    api_key = str(env.get("MSTOCK_STREAM_API_KEY", "")).strip()
    access_token = str(env.get("MSTOCK_STREAM_ACCESS_TOKEN", "")).strip()
    endpoint = str(env.get("MSTOCK_STREAM_URL", DEFAULT_MSTOCK_STREAM_URL)).strip()
    try:
        tokens = _parse_tokens(str(env.get("MSTOCK_STREAM_INSTRUMENT_TOKENS", "")))
    except ValueError as exc:
        return {"enabled": enabled, "configured": False, "reason": str(exc), "tokens": []}
    configured = bool(api_key and access_token and tokens and endpoint.startswith("wss://"))
    reason = None
    if enabled and not configured:
        reason = "Set the stream API key, access token, WSS endpoint and instrument token subscriptions."
    return {
        "enabled": enabled,
        "configured": configured,
        "reason": reason,
        "api_key": api_key,
        "access_token": access_token,
        "endpoint": endpoint,
        "tokens": tokens,
    }


def build_stream_url(endpoint: str, api_key: str, access_token: str) -> str:
    if not endpoint.startswith("wss://"):
        raise ValueError("m.Stock streaming requires a secure WSS endpoint.")
    separator = "&" if "?" in endpoint else "?"
    return endpoint + separator + urlencode({"API_KEY": api_key, "ACCESS_TOKEN": access_token})


class _WebSocketClientAdapter:
    def __init__(self, socket):
        self._socket = socket

    def send(self, value):
        return self._socket.send(value)

    def recv(self):
        import websocket
        try:
            return self._socket.recv()
        except websocket.WebSocketTimeoutException as exc:
            raise TimeoutError("Market stream receive timeout") from exc

    def close(self):
        return self._socket.close()


class MStockStreamRuntime:
    def __init__(self):
        self._worker: MarketStreamWorker | None = None
        self._configuration: dict = {"enabled": False, "configured": False, "reason": "Streaming is disabled."}

    def start(self) -> dict:
        config = get_stream_config()
        self._configuration = {key: value for key, value in config.items() if key not in {"api_key", "access_token"}}
        if not config["enabled"] or not config["configured"]:
            return self.status()
        api_key = config["api_key"]
        endpoint = config["endpoint"]
        receive_timeout = float(os.getenv("MSTOCK_STREAM_RECEIVE_TIMEOUT", "2"))

        def token_provider():
            # Re-read the token on each reconnect so an operator can rotate it
            # without restarting the Financial OS process.
            return os.getenv("MSTOCK_STREAM_ACCESS_TOKEN", "").strip() or None

        def socket_factory(token):
            import websocket
            url = build_stream_url(endpoint, api_key, token)
            socket = websocket.create_connection(
                url,
                timeout=receive_timeout,
                enable_multithread=True,
                suppress_origin=True,
            )
            socket.settimeout(receive_timeout)
            return _WebSocketClientAdapter(socket)

        self._worker = MarketStreamWorker(
            token_provider=token_provider,
            socket_factory=socket_factory,
            token_subscriptions=config["tokens"],
            receive_timeout=receive_timeout,
            stale_after=float(os.getenv("MSTOCK_STREAM_STALE_AFTER", "15")),
        )
        self._worker.start()
        return self.status()

    def stop(self):
        if self._worker is not None:
            self._worker.stop()
        return self.status()

    def status(self) -> dict:
        worker_status = self._worker.status() if self._worker is not None else {
            "running": False, "connected": False, "last_tick_at": None,
            "last_tick_age_seconds": None, "stale": True, "last_error": None,
            "reconnect_count": 0, "cached_ticks": 0, "read_only": True,
        }
        return {
            "enabled": bool(self._configuration.get("enabled")),
            "configured": bool(self._configuration.get("configured")),
            "configuration_reason": self._configuration.get("reason"),
            "subscribed_instruments": len(self._configuration.get("tokens", [])),
            **worker_status,
        }

    def snapshot(self) -> dict:
        status = self.status()
        ticks = self._worker.snapshot()["ticks"] if self._worker is not None else []
        return {"status": status, "ticks": ticks, "read_only": True, "database_write": False}


market_stream_runtime = MStockStreamRuntime()
