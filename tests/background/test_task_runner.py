"""G6: off-thread task execution and main-thread result marshalling."""

from __future__ import annotations

import threading
from collections.abc import Iterator

import pytest

from market_monitor_gui.background.task_runner import TaskRunner

pytestmark = pytest.mark.unit


@pytest.fixture
def runner() -> Iterator[TaskRunner]:
    instance = TaskRunner(max_workers=2)
    yield instance
    instance.shutdown()


def test_success_callback_runs_on_drain_thread(runner: TaskRunner) -> None:
    results: list[str] = []
    worker_threads: list[str] = []

    def work() -> str:
        worker_threads.append(threading.current_thread().name)
        return "ok"

    handle = runner.submit(work, on_ok=results.append, on_err=lambda exc: results.append("err"))
    assert handle is not None
    assert runner.wait_idle(5.0) is True

    assert results == []  # nothing delivered until drain()
    assert runner.drain() == 1
    assert results == ["ok"]
    assert worker_threads and worker_threads[0] != threading.current_thread().name


def test_error_routes_to_on_err(runner: TaskRunner) -> None:
    seen: list[BaseException] = []

    def boom() -> None:
        raise RuntimeError("nope")

    runner.submit(
        boom, on_ok=lambda value: seen.append(AssertionError("unexpected")), on_err=seen.append
    )
    assert runner.wait_idle(5.0) is True
    runner.drain()

    assert len(seen) == 1
    assert isinstance(seen[0], RuntimeError)


def test_duplicate_key_is_suppressed_while_pending(runner: TaskRunner) -> None:
    gate = threading.Event()

    def slow() -> str:
        gate.wait(5.0)
        return "first"

    first = runner.submit(slow, on_ok=lambda value: None, on_err=lambda exc: None, key="k")
    assert first is not None
    assert runner.is_running("k") is True

    second = runner.submit(
        lambda: "second", on_ok=lambda value: None, on_err=lambda exc: None, key="k"
    )
    assert second is None

    gate.set()
    assert runner.wait_idle(5.0) is True
    assert runner.is_running("k") is False

    third = runner.submit(
        lambda: "third", on_ok=lambda value: None, on_err=lambda exc: None, key="k"
    )
    assert third is not None
    runner.wait_idle(5.0)


def test_cancel_suppresses_result_delivery(runner: TaskRunner) -> None:
    gate = threading.Event()
    delivered: list[str] = []

    def slow() -> str:
        gate.wait(5.0)
        return "late"

    handle = runner.submit(slow, on_ok=delivered.append, on_err=lambda exc: delivered.append("err"))
    assert handle is not None
    handle.cancel()
    assert handle.cancelled is True

    gate.set()
    assert runner.wait_idle(5.0) is True
    assert runner.drain() == 0
    assert delivered == []


def test_cancel_before_start_returns_true() -> None:
    runner = TaskRunner(max_workers=1)
    gate = threading.Event()
    blocker = runner.submit(
        lambda: gate.wait(5.0), on_ok=lambda value: None, on_err=lambda exc: None
    )
    assert blocker is not None

    queued = runner.submit(lambda: "never", on_ok=lambda value: None, on_err=lambda exc: None)
    assert queued is not None
    assert queued.cancel() is True

    gate.set()
    runner.shutdown()


def test_shutdown_drops_outstanding_results(runner: TaskRunner) -> None:
    gate = threading.Event()
    delivered: list[str] = []

    def slow() -> str:
        gate.wait(5.0)
        return "late"

    runner.submit(slow, on_ok=delivered.append, on_err=lambda exc: delivered.append("err"))
    runner.shutdown(wait=False, cancel_pending=True)
    gate.set()

    assert runner.drain() == 0
    assert delivered == []
    assert runner.submit(lambda: None, on_ok=lambda value: None, on_err=lambda exc: None) is None


def test_post_runs_on_next_drain(runner: TaskRunner) -> None:
    seen: list[str] = []
    runner.post(lambda: seen.append("posted"))
    assert runner.pending_count() == 1
    assert runner.drain() == 1
    assert seen == ["posted"]


def test_post_after_shutdown_is_dropped(runner: TaskRunner) -> None:
    runner.shutdown()
    runner.post(lambda: None)
    assert runner.pending_count() == 0
