"""Opt-in m.Stock Type A WebSocket runtime.

Credentials are read only from backend environment configuration. The stream is
read-only and remains disabled unless explicitly enabled with valid credentials
and instrument tokens. No broker order APIs are used.
"""
from __future__ import annotations

import csv
import os
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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


def parse_instrument_metadata(csv_text: str, tokens: list[int]) -> dict[int, dict]:
    """Resolve only subscribed Type A tokens against the gateway script master."""
    requested = {int(token) for token in tokens}
    if not requested:
        return {}
    reader = csv.DictReader(StringIO(str(csv_text).lstrip("\\ufeff")))
    if not reader.fieldnames:
        return {}
    columns = {
        "".join(char for char in name.lower() if char.isalnum()): name
        for name in reader.fieldnames
    }

    def field(row, *names):
        for name in names:
            actual = columns.get("".join(char for char in name.lower() if char.isalnum()))
            if actual:
                value = str(row.get(actual) or "").strip()
                if value:
                    return value
        return None

    mapped = {}
    for row in reader:
        raw_token = field(row, "instrument_token", "token")
        try:
            token = int(raw_token) if raw_token else None
        except ValueError:
            continue
        if token not in requested:
            continue
        symbol = field(row, "tradingsymbol", "symbol", "trading_symbol")
        exchange = field(row, "exchange", "exch")
        if not symbol or not exchange:
            continue
        exchange = exchange.upper()
        mapped[token] = {
            "symbol": symbol,
            "name": field(row, "name", "company_name") or symbol,
            "exchange": exchange,
            "segment": field(row, "segment", "instrument_type"),
            "instrument_key": f"{exchange}:{symbol}",
            "expiry": field(row, "expiry"),
            "strike": field(row, "strike"),
        }
    return mapped


def _fetch_instrument_metadata(tokens: list[int]) -> dict[int, dict]:
    gateway = os.getenv("MSTOCK_GATEWAY_URL", "").strip().rstrip("/")
    if not gateway or not tokens:
        return {}
    headers = {"Accept": "text/csv"}
    secret = os.getenv("MSTOCK_GATEWAY_SECRET", "").strip()
    if secret:
        headers["X-Financial-OS-Gateway-Secret"] = secret
    request = Request(f"{gateway}/instruments", headers=headers, method="GET")
    try:
        with urlopen(request, timeout=8) as response:
            if response.status != 200:
                return {}
            return parse_instrument_metadata(response.read().decode("utf-8", errors="replace"), tokens)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return {}


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
        self._configuration: dict = {"enabled": False, "configured": False, "reason": "Streaming is disabled."}\n        self._instrument_metadata: dict[int, dict] = {}\n        self._metadata_error: str | None = None

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
