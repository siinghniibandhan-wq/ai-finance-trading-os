"""Read-only m.Stock Type A SDK market-stream worker.

This mirrors the production gateway architecture: one MTicker instance is shared
by the market-stream routes and the Order Flow adapter. A market-data tick for a
currently subscribed token is the stream-verification signal; sending LOGIN is
not treated as an authentication acknowledgement.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable


_MODE_NAMES = {1: "ltp", 2: "quote", 3: "full"}
_SDK_MODES = {1: "MODE_LTP", 2: "MODE_QUOTE", 3: "MODE_FULL"}


class MarketStreamWorker:
    def __init__(
        self,
        token_getter: Callable[[], str | None],
        api_key_getter: Callable[[], str],
        max_cache: int = 5000,
        stale_after: int = 30,
    ):
        self.token_getter = token_getter
        self.api_key_getter = api_key_getter
        self.max_cache = max_cache
        self.stale_after = stale_after
        self._lock = threading.RLock()
        self._ticker: Any = None
        self._tokens: list[int] = []
        self._mode = 3
        self._ticks: OrderedDict[int, dict] = OrderedDict()
        self._running = False
        self._socket_connected = False
        self._stream_verified = False
        self._last_message = None
        self._last_tick_at = None
        self._last_error = None
        self._reconnect_count = 0
        self._connection_generation = 0
        self._subscription_generation = 0

    def start(self, tokens: list[int], mode: int = 3):
        clean = list(dict.fromkeys(int(token) for token in tokens))
        if not clean or len(clean) > 200 or any(token <= 0 for token in clean):
            raise ValueError("Provide between 1 and 200 positive instrument tokens")
        if mode not in _MODE_NAMES:
            raise ValueError("Mode must be 1 (LTP), 2 (quote), or 3 (full)")
        with self._lock:
            changed = clean != self._tokens or mode != self._mode
            if self._running and self._ticker is not None:
                if changed:
                    self._invalidate_stream_locked()
                    self._tokens = clean
                    self._mode = mode
                    self._subscription_generation += 1
                    ticker = self._ticker
                    removed = list(set(self._ticker_tokens) - set(clean)) if hasattr(self, "_ticker_tokens") else []
                    added = [token for token in clean if token not in getattr(self, "_ticker_tokens", [])]
                    self._ticker_tokens = clean[:]
                    try:
                        if removed and hasattr(ticker, "unsubscribe"):
                            ticker.unsubscribe(removed)
                        if added:
                            ticker.subscribe(added)
                        sdk_mode = getattr(ticker, _SDK_MODES[mode])
                        ticker.set_mode(sdk_mode, clean)
                    except Exception as exc:
                        self._last_error = "Subscription update failed: " + str(exc)[:240]
                        self._socket_connected = False
                        raise RuntimeError("Unable to update m.Stock subscriptions") from exc
                return {"started": True, "already_running": True, "reconnecting": False}

            token = self.token_getter()
            api_key = self.api_key_getter()
            if not token or not api_key:
                raise RuntimeError("m.Stock authentication and API key are required")
            from tradingapi_a.mticker import MTicker

            self._tokens = clean
            self._mode = mode
            self._ticker_tokens = clean[:]
            self._subscription_generation += 1
            self._invalidate_stream_locked()
            self._running = True
            self._last_error = None
            ticker = MTicker(
                api_key,
                token,
                root="wss://ws.mstock.trade",
                reconnect=True,
                reconnect_max_tries=50,
                reconnect_max_delay=60,
                connect_timeout=30,
            )
            self._ticker = ticker
            ticker.on_connect = self._on_connect
            ticker.on_open = self._on_open
            ticker.on_ticks = self._on_ticks
            ticker.on_message = self._on_message
            ticker.on_error = self._on_error
            ticker.on_close = self._on_close
            ticker.on_reconnect = self._on_reconnect
            ticker.on_noreconnect = self._on_noreconnect
        try:
            ticker.connect(threaded=True)
        except Exception as exc:
            with self._lock:
                self._running = False
                self._ticker = None
                self._invalidate_stream_locked()
                self._last_error = "m.Stock stream connection failed: " + str(exc)[:240]
            raise RuntimeError("Unable to connect m.Stock market stream") from exc
        return {"started": True, "already_running": False, "read_only": True}

    def _invalidate_stream_locked(self):
        self._connection_generation += 1
        self._socket_connected = False
        self._stream_verified = False
        self._last_tick_at = None
        self._ticks.clear()

    def _on_connect(self, ticker, response=None):
        try:
            sent = ticker.send_login_after_connect()
            if sent is False:
                raise RuntimeError("m.Stock LOGIN frame could not be sent")
            with self._lock:
                tokens = self._tokens[:]
                mode = self._mode
            if not getattr(ticker, "subscribed_tokens", {}):
                ticker.subscribe(tokens)
            ticker.set_mode(getattr(ticker, _SDK_MODES[mode]), tokens)
            with self._lock:
                self._socket_connected = True
                self._stream_verified = False
                self._last_tick_at = None
                self._ticks.clear()
        except Exception as exc:
            self._on_error(ticker, exc)
            raise

    def _on_open(self, ticker):
        with self._lock:
            self._socket_connected = True
            self._stream_verified = False
            self._last_tick_at = None
            self._ticks.clear()

    def _on_ticks(self, ticker, ticks):
        received_at = time.time()
        with self._lock:
            subscribed = set(self._tokens)
            accepted = 0
            for tick in ticks or []:
                if not isinstance(tick, dict):
                    continue
                token = tick.get("instrument_token", tick.get("token"))
                try:
                    token = int(token)
                except (TypeError, ValueError):
                    continue
                if token not in subscribed:
                    continue
                normalized = dict(tick)
                normalized["instrument_token"] = token
                normalized["token"] = token
                normalized["received_at"] = received_at
                self._ticks[token] = normalized
                self._ticks.move_to_end(token)
                accepted += 1
            while len(self._ticks) > self.max_cache:
                self._ticks.popitem(last=False)
            if accepted:
                self._last_tick_at = received_at
                self._stream_verified = True
                self._socket_connected = True

    def _on_message(self, ticker, message):
        with self._lock:
            self._last_message = str(message)[:300]

    def _on_error(self, ticker, error):
        with self._lock:
            self._last_error = str(error)[:300]
            self._socket_connected = False
            self._stream_verified = False
            self._last_tick_at = None
            self._ticks.clear()

    def _on_close(self, ticker, code=None, reason=None):
        with self._lock:
            self._socket_connected = False
            self._stream_verified = False
            self._last_tick_at = None
            self._ticks.clear()

    def _on_reconnect(self, ticker, attempt_count=0):
        with self._lock:
            self._reconnect_count = max(self._reconnect_count + 1, int(attempt_count or 0))
            self._invalidate_stream_locked()

    def _on_noreconnect(self, ticker):
        with self._lock:
            self._running = False
            self._invalidate_stream_locked()

    def stop(self, timeout: float = 3):
        with self._lock:
            ticker = self._ticker
            self._running = False
            self._invalidate_stream_locked()
        if ticker is not None:
            try:
                ticker.close()
            except Exception as exc:
                with self._lock:
                    self._last_error = "m.Stock stream close failed: " + str(exc)[:240]
        return {"stopped": True}

    def status(self):
        with self._lock:
            age = None if self._last_tick_at is None else max(0, time.time() - self._last_tick_at)
            stale = age is None or age > self.stale_after
            verified = self._stream_verified and not stale
            connected = self._running and self._socket_connected and verified
            return {
                "running": self._running,
                "connected": connected,
                "socket_connected": self._socket_connected,
                "stream_verified": verified,
                "authentication_status": "verified_by_market_data" if verified else "unverified",
                "last_message": self._last_message,
                "subscribed_tokens": self._tokens[:],
                "mode": self._mode,
                "mode_name": _MODE_NAMES[self._mode],
                "cached_instruments": len(self._ticks),
                "last_tick_at": self._last_tick_at,
                "last_tick_age_seconds": age,
                "stale": stale,
                "last_error": self._last_error,
                "reconnect_count": self._reconnect_count,
                "read_only": True,
            }

    def snapshot(self, tokens: list[int] | None = None):
        with self._lock:
            selected = set(int(token) for token in tokens) if tokens else None
            return [
                dict(tick) for token, tick in self._ticks.items()
                if selected is None or token in selected
            ]
