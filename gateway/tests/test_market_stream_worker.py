import sys
import time
import types

import pytest

from market_stream import MarketStreamWorker


class FakeTicker:
    MODE_LTP = 1
    MODE_QUOTE = 2
    MODE_FULL = 3
    instances = []

    def __init__(self, api_key, access_token, **kwargs):
        self.api_key = api_key
        self.access_token = access_token
        self.kwargs = kwargs
        self.subscribed_tokens = {}
        self.calls = []
        self.closed = False
        type(self).instances.append(self)

    def send_login_after_connect(self):
        self.calls.append(("login",))
        return True

    def connect(self, threaded=False):
        self.calls.append(("connect", threaded))
        self.on_open(self)
        self.on_connect(self, {"status": "connected"})

    def subscribe(self, tokens):
        self.calls.append(("subscribe", list(tokens)))
        for token in tokens:
            self.subscribed_tokens[token] = self.MODE_QUOTE

    def unsubscribe(self, tokens):
        self.calls.append(("unsubscribe", list(tokens)))
        for token in tokens:
            self.subscribed_tokens.pop(token, None)

    def set_mode(self, mode, tokens):
        self.calls.append(("set_mode", mode, list(tokens)))

    def close(self):
        self.closed = True
        self.on_close(self, 1000, "closed")


@pytest.fixture
def sdk(monkeypatch):
    FakeTicker.instances.clear()
    package = types.ModuleType("tradingapi_a")
    module = types.ModuleType("tradingapi_a.mticker")
    module.MTicker = FakeTicker
    package.mticker = module
    monkeypatch.setitem(sys.modules, "tradingapi_a", package)
    monkeypatch.setitem(sys.modules, "tradingapi_a.mticker", module)
    return FakeTicker


def make_worker(**kwargs):
    return MarketStreamWorker(lambda: "access-token", lambda: "api-key", **kwargs)


def test_worker_uses_production_mstock_sdk_and_subscribes_after_login(sdk):
    worker = make_worker()
    result = worker.start([123])
    ticker = sdk.instances[-1]
    assert result["started"] is True
    assert ticker.access_token == "access-token"
    assert ticker.kwargs["root"] == "wss://ws.mstock.trade"
    assert ("login",) in ticker.calls
    assert ("subscribe", [123]) in ticker.calls
    assert ("set_mode", FakeTicker.MODE_FULL, [123]) in ticker.calls
    assert worker.status()["connected"] is False  # socket alone is not feed verification
    worker.stop()


def test_only_tick_for_current_subscription_verifies_stream(sdk):
    worker = make_worker()
    worker.start([123])
    ticker = sdk.instances[-1]
    worker._on_ticks(ticker, [{"instrument_token": 999, "last_price": 1}])
    assert worker.status()["stream_verified"] is False
    assert worker.snapshot() == []
    worker._on_ticks(ticker, [{"instrument_token": 123, "last_price": 456, "oi": 12}])
    status = worker.status()
    assert status["stream_verified"] is True
    assert status["connected"] is True
    assert worker.snapshot()[0]["last_price"] == 456
    worker.stop()


def test_reconnect_invalidates_previous_verification_and_cached_ticks(sdk):
    worker = make_worker()
    worker.start([123])
    ticker = sdk.instances[-1]
    worker._on_ticks(ticker, [{"instrument_token": 123, "last_price": 456}])
    assert worker.status()["connected"] is True
    worker._on_reconnect(ticker, 1)
    status = worker.status()
    assert status["connected"] is False
    assert status["stream_verified"] is False
    assert status["last_tick_at"] is None
    assert worker.snapshot() == []
    worker.stop()


def test_subscription_change_invalidates_old_ticks_and_verification(sdk):
    worker = make_worker()
    worker.start([123])
    ticker = sdk.instances[-1]
    worker._on_ticks(ticker, [{"instrument_token": 123, "last_price": 456}])
    assert worker.status()["connected"] is True
    worker.start([456])
    status = worker.status()
    assert status["connected"] is False
    assert status["stream_verified"] is False
    assert worker.snapshot() == []
    assert ("unsubscribe", [123]) in ticker.calls
    assert ("subscribe", [456]) in ticker.calls
    worker.stop()


def test_stale_feed_is_never_connected(sdk):
    worker = make_worker(stale_after=0)
    worker.start([123])
    ticker = sdk.instances[-1]
    worker._on_ticks(ticker, [{"instrument_token": 123, "last_price": 456}])
    time.sleep(.01)
    status = worker.status()
    assert status["stale"] is True
    assert status["connected"] is False
    assert status["stream_verified"] is False
    worker.stop()


def test_close_and_error_invalidate_stream_state(sdk):
    worker = make_worker()
    worker.start([123])
    ticker = sdk.instances[-1]
    worker._on_ticks(ticker, [{"instrument_token": 123, "last_price": 456}])
    worker._on_close(ticker, 1006, "connection lost")
    assert worker.status()["connected"] is False
    assert worker.snapshot() == []
    worker._on_ticks(ticker, [{"instrument_token": 123, "last_price": 457}])
    worker._on_error(ticker, RuntimeError("provider error"))
    assert worker.status()["stream_verified"] is False
    assert worker.snapshot() == []
    worker.stop()


def test_worker_validates_subscription_bounds(sdk):
    worker = make_worker()
    for tokens in ([], [0], list(range(1, 202))):
        with pytest.raises(ValueError):
            worker.start(tokens)


def test_worker_requires_gateway_authentication(sdk):
    worker = MarketStreamWorker(lambda: None, lambda: "api-key")
    with pytest.raises(RuntimeError, match="authentication"):
        worker.start([123])
