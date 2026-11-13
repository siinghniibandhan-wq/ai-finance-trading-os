"""Additive, read-only persistent m.Stock Type A stream worker.

The caller supplies the authenticated-token provider and WebSocket factory so
this worker can be hosted beside an existing gateway without owning its auth,
HTTP routes, database, or trading lifecycle. It never starts on import.
"""
from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable

from app.services.mstock_stream import parse_type_a_frame


class MarketStreamWorker:
    def __init__(
        self,
        *,
        token_provider: Callable[[], str | None],
        socket_factory: Callable[[str], Any],
        token_subscriptions: list[int] | None = None,
        max_ticks: int = 5000,
        stale_after: float = 15.0,
        receive_timeout: float = 1.0,
        reconnect_min: float = 1.0,
        reconnect_max: float = 30.0,
    ) -> None:
        if max_ticks < 1:
            raise ValueError("max_ticks must be positive")
        if stale_after <= 0 or receive_timeout <= 0:
            raise ValueError("stale_after and receive_timeout must be positive")
        if reconnect_min <= 0 or reconnect_max < reconnect_min:
            raise ValueError("invalid reconnect backoff bounds")
        self._token_provider = token_provider
        self._socket_factory = socket_factory
        self._subscriptions = list(dict.fromkeys(token_subscriptions or []))
        self._max_ticks = max_ticks
        self._stale_after = stale_after
        self._receive_timeout = receive_timeout
        self._reconnect_min = reconnect_min
        self._reconnect_max = reconnect_max
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket: Any = None
        self._ticks: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._connected = False
        self._running = False
        self._last_tick_at: float | None = None
        self._last_error: str | None = None
        self._reconnect_count = 0

    def start(self) -> bool:
        """Start explicitly; repeated starts are idempotent."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._running = True
            self._thread = threading.Thread(
                target=self._run, name="mstock-market-stream", daemon=True
            )
            self._thread.start()
            return True

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        with self._lock:
            sock = self._socket
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, timeout))
        with self._lock:
            if not thread or not thread.is_alive():
                self._running = False
                self._connected = False
                self._socket = None

    def _run(self) -> None:
        delay = self._reconnect_min
        try:
            while not self._stop_event.is_set():
                token = self._token_provider()
                if not token:
                    self._set_error("Waiting for a valid m.Stock access token")
                    self._stop_event.wait(delay)
                    continue
                sock = None
                try:
                    sock = self._socket_factory(token)
                    with self._lock:
                        self._socket = sock
                        self._connected = True
                        self._last_error = None
                    sock.send(f"LOGIN:{token}")
                    if self._subscriptions:
                        sock.send(json.dumps({"a": "subscribe", "v": self._subscriptions}))
                    delay = self._reconnect_min
                    while not self._stop_event.is_set():
                        try:
                            frame = sock.recv()
                        except TimeoutError:
                            continue
                        if isinstance(frame, str):
                            # Text heartbeats/control messages are not market ticks.
                            continue
                        ticks = parse_type_a_frame(frame)
                        if ticks:
                            self._store_ticks(ticks)
                except Exception as exc:
                    if not self._stop_event.is_set():
                        self._set_error(type(exc).__name__)
                        with self._lock:
                            self._reconnect_count += 1
                finally:
                    if sock is not None:
                        try:
                            sock.close()
                        except Exception:
                            pass
                    with self._lock:
                        if self._socket is sock:
                            self._socket = None
                        self._connected = False
                if not self._stop_event.is_set():
                    self._stop_event.wait(delay)
                    delay = min(delay * 2, self._reconnect_max)
        finally:
            with self._lock:
                self._running = False
                self._connected = False
                self._socket = None

    def _set_error(self, message: str) -> None:
        with self._lock:
            self._last_error = message

    def _store_ticks(self, ticks: list[dict[str, Any]]) -> None:
        now = time.time()
        with self._lock:
            for tick in ticks:
                token = tick.get("token")
                if token is None:
                    continue
                self._ticks[token] = deepcopy(tick)
                self._ticks.move_to_end(token)
                while len(self._ticks) > self._max_ticks:
                    self._ticks.popitem(last=False)
            if ticks:
                self._last_tick_at = now

    def status(self) -> dict[str, Any]:
        with self._lock:
            age = None if self._last_tick_at is None else max(0.0, time.time() - self._last_tick_at)
            return {
                "running": self._running,
                "connected": self._connected,
                "last_tick_at": self._last_tick_at,
                "last_tick_age_seconds": age,
                "stale": age is None or age > self._stale_after,
                "last_error": self._last_error,
                "reconnect_count": self._reconnect_count,
                "cached_ticks": len(self._ticks),
                "read_only": True,
            }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": self.status(),
                "ticks": deepcopy(list(self._ticks.values())),
            }
