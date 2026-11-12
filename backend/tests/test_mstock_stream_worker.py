import threading
import time

from app.services.mstock_stream_worker import MarketStreamWorker


class FakeSocket:
    def __init__(self, frames=None):
        self.frames = list(frames or [])
        self.sent = []
        self.closed = False

    def send(self, value):
        self.sent.append(value)

    def recv(self):
        if self.frames:
            return self.frames.pop(0)
        raise TimeoutError("no frame")

    def close(self):
        self.closed = True


def test_worker_starts_only_when_explicitly_started_and_stops_cleanly():
    socket = FakeSocket()
    worker = MarketStreamWorker(
        token_provider=lambda: "test-token",
        socket_factory=lambda token: socket,
        token_subscriptions=[101],
        receive_timeout=0.01,
    )

    assert worker.status()["running"] is False
    worker.start()
    deadline = time.monotonic() + 1
    while not socket.sent and time.monotonic() < deadline:
        time.sleep(0.005)
    assert worker.status()["running"] is True
    worker.stop(timeout=1)
    assert worker.status()["running"] is False
    assert socket.sent[0] == "LOGIN:test-token"
    assert '"subscribe"' in socket.sent[1]
    assert socket.closed is True


def test_worker_cache_is_bounded_and_snapshot_is_read_only():
    worker = MarketStreamWorker(
        token_provider=lambda: "test-token",
        socket_factory=lambda token: FakeSocket(),
        token_subscriptions=[],
        max_ticks=2,
    )
    worker._store_ticks([
        {"token": 1, "ltp_raw": 100},
        {"token": 2, "ltp_raw": 200},
        {"token": 3, "ltp_raw": 300},
    ])

    snapshot = worker.snapshot()
    assert [tick["token"] for tick in snapshot["ticks"]] == [2, 3]
    snapshot["ticks"][0]["ltp_raw"] = -1
    assert worker.snapshot()["ticks"][0]["ltp_raw"] == 200


def test_worker_reports_disconnected_and_never_starts_implicitly():
    worker = MarketStreamWorker(
        token_provider=lambda: None,
        socket_factory=lambda token: FakeSocket(),
    )

    status = worker.status()
    assert status["connected"] is False
    assert status["running"] is False
    assert status["last_error"] is None
