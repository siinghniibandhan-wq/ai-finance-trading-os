"""Read-only persistent m.Stock Type A stream worker for the Flask gateway."""
from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Callable, Any

from mstock_stream import parse_type_a_frame


class MarketStreamWorker:
    def __init__(self, token_getter: Callable[[], str | None], api_key_getter: Callable[[], str],
                 websocket_factory: Callable[..., Any] | None = None, max_cache: int = 5000,
                 stale_after: int = 30, recv_timeout: int = 5):
        self.token_getter = token_getter
        self.api_key_getter = api_key_getter
        self.websocket_factory = websocket_factory
        self.max_cache = max_cache
        self.stale_after = stale_after
        self.recv_timeout = recv_timeout
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._ws = None
        self._tokens: list[int] = []
        self._mode = 3
        self._subscription_revision = 0
        self._ticks: OrderedDict[int, dict] = OrderedDict()
        self._connected = False
        self._socket_connected = False
        self._stream_verified = False
        self._last_tick_at = None
        self._last_error = None
        self._reconnect_count = 0

    def start(self, tokens: list[int], mode: int = 3):
        clean = list(dict.fromkeys(int(t) for t in tokens))
        if not clean or len(clean) > 200 or any(t <= 0 for t in clean):
            raise ValueError("Provide between 1 and 200 positive instrument tokens")
        if mode not in (1, 2, 3):
            raise ValueError("Mode must be 1 (LTP), 2 (quote), or 3 (full)")
        with self._lock:
            changed = clean != self._tokens or mode != self._mode
            self._tokens, self._mode = clean, mode
            if changed:
                self._subscription_revision += 1
                self._ticks.clear()
                self._last_tick_at = None
                self._stream_verified = False
                self._connected = False
            if self._thread and self._thread.is_alive():
                ws = self._ws
                if changed and ws:
                    try:
                        ws.close()
                    except Exception:
                        pass
                return {"started": True, "already_running": True, "reconnecting": bool(changed)}
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="mstock-market-stream", daemon=True)
            self._thread.start()
        return {"started": True, "already_running": False}

    def stop(self, timeout: float = 3):
        self._stop.set()
        with self._lock:
            ws = self._ws
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout)
        with self._lock:
            self._connected = False
            self._socket_connected = False
            self._stream_verified = False
            self._last_tick_at = None
            self._ticks.clear()
        return {"stopped": not bool(thread and thread.is_alive())}

    def _run(self):
        delay = 1
        while not self._stop.is_set():
            ws = None
            try:
                token = self.token_getter()
                if not token:
                    raise RuntimeError("m.Stock authentication required; waiting for gateway re-authentication")
                import websocket
                factory = self.websocket_factory or websocket.create_connection
                api_key = self.api_key_getter()
                ws = factory(f"wss://ws.mstock.trade?API_KEY={api_key}&ACCESS_TOKEN={token}", timeout=self.recv_timeout)
                with self._lock:
                    self._ws = ws
                    self._socket_connected = True
                    self._stream_verified = False
                    self._connected = False
                    self._last_tick_at = None
                    self._ticks.clear()
                    self._last_error = None
                    initial_tokens = self._tokens[:]
                    subscribed_revision = self._subscription_revision
                # A successful LOGIN send is not provider authentication.
                # A tick for a subscribed instrument is the verification signal.
                ws.send(f"LOGIN:{token}")
                ws.send(json.dumps({"a": "subscribe", "v": initial_tokens}))
                delay = 1
                while not self._stop.is_set():
                    if self.token_getter() != token:
                        raise RuntimeError("m.Stock access token changed; reconnecting")
                    with self._lock:
                        revision = self._subscription_revision
                    if revision != subscribed_revision:
                        raise RuntimeError("m.Stock subscription set changed; reconnecting")
                    try:
                        frame = ws.recv()
                    except Exception as exc:
                        if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
                            continue
                        raise
                    if isinstance(frame, str):
                        continue
                    for tick in parse_type_a_frame(frame):
                        instrument = int(tick["token"])
                        with self._lock:
                            if instrument not in self._tokens:
                                continue
                            received_at = time.time()
                            self._ticks[instrument] = {
                                **tick, "instrument_token": instrument,
                                "received_at": received_at,
                            }
                            self._ticks.move_to_end(instrument)
                            while len(self._ticks) > self.max_cache:
                                self._ticks.popitem(last=False)
                            self._last_tick_at = received_at
                            self._stream_verified = True
                            self._connected = True
            except Exception as exc:
                with self._lock:
                    self._last_error = str(exc)[:300]
                    self._reconnect_count += 1
            finally:
                with self._lock:
                    self._connected = False
                    self._socket_connected = False
                    self._stream_verified = False
                    self._last_tick_at = None
                    self._ticks.clear()
                    self._ws = None
                if ws:
                    try:
                        ws.close()
                    except Exception:
                        pass
            self._stop.wait(delay)
            delay = min(delay * 2, 30)

    def status(self):
        with self._lock:
            age = None if self._last_tick_at is None else max(0, time.time() - self._last_tick_at)
            stale = age is None or age > self.stale_after
            verified = self._stream_verified and not stale
            connected = self._socket_connected and verified
            return {
                "connected": connected,
                "socket_connected": self._socket_connected,
                "stream_verified": verified,
                "subscribed_tokens": self._tokens[:],
                "mode": self._mode,
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
            selected = set(int(t) for t in tokens) if tokens else None
            return [dict(v) for k, v in self._ticks.items() if selected is None or k in selected]
