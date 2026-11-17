import struct
import time

from market_stream import MarketStreamWorker


class FakeSocket:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.sent = []
        self.closed = False

    def send(self, value):
        self.sent.append(value)

    def recv(self):
        try:
            return next(self.frames)
        except StopIteration:
            raise RuntimeError("socket closed")

    def close(self):
        self.closed = True


def frame_ltp(token=123, ltp=456):
    packet = struct.pack(">2I", token, ltp)
    return struct.pack(">H", 1) + struct.pack(">H", len(packet)) + packet


def wait_for(predicate, timeout=1):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(.01)
    return bool(predicate())


def test_worker_waits_for_login_ack_before_subscribing_and_caches_ticks():
    sock = FakeSocket(['{"status":"success"}', frame_ltp()])
    worker = MarketStreamWorker(lambda: "token", lambda: "key",
                                websocket_factory=lambda *a, **k: sock, recv_timeout=1)
    worker.start([123])
    assert wait_for(lambda: bool(worker.snapshot()))
    ticks = worker.snapshot()
    assert ticks[0]["token"] == 123 and ticks[0]["ltp_raw"] == 456
    assert sock.sent[0] == "LOGIN:token"
    assert sock.sent[1] == '{"a": "subscribe", "v": [123]}'
    assert worker.status()["connected"] is True
    assert worker.status()["cached_instruments"] == 1
    worker.stop()


def test_worker_rejects_unsafe_or_oversized_subscriptions():
    worker = MarketStreamWorker(lambda: None, lambda: "key")
    for tokens in ([], [0], list(range(1, 202))):
        try:
            worker.start(tokens)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid token list accepted")


def test_worker_rejects_login_failure_without_subscribing():
    sock = FakeSocket(['{"status":"error","message":"invalid token"}'])
    worker = MarketStreamWorker(lambda: "token", lambda: "key",
                                websocket_factory=lambda *a, **k: sock, recv_timeout=1)
    worker.start([123])
    assert wait_for(lambda: worker.status()["last_error"] is not None)
    assert worker.status()["connected"] is False
    assert sock.sent == ["LOGIN:token"]
    worker.stop()


def test_worker_rejects_binary_frame_as_login_ack():
    sock = FakeSocket([frame_ltp()])
    worker = MarketStreamWorker(lambda: "token", lambda: "key",
                                websocket_factory=lambda *a, **k: sock, recv_timeout=1)
    worker.start([123])
    assert wait_for(lambda: worker.status()["last_error"] is not None)
    assert worker.status()["connected"] is False
    assert sock.sent == ["LOGIN:token"]
    worker.stop()


def test_worker_accepts_login_ack_with_type_and_message_fields():
    sock = FakeSocket(['{"type":"login","message":"success"}', frame_ltp()])
    worker = MarketStreamWorker(lambda: "token", lambda: "key",
                                websocket_factory=lambda *a, **k: sock, recv_timeout=1)
    worker.start([123])
    assert wait_for(lambda: bool(worker.snapshot()))
    assert sock.sent[0] == "LOGIN:token"
    assert sock.sent[1] == '{"a": "subscribe", "v": [123]}'
    worker.stop()
