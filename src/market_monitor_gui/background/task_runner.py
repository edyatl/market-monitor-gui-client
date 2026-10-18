"""Run callables off the UI thread and marshal results back to the main thread.

This module is deliberately **Tkinter-free**. Workers run on a small thread pool and
only enqueue callbacks onto a thread-safe queue; the Tk shell owns the event loop and
calls :meth:`TaskRunner.drain` on the main thread (scheduled with ``root.after``). No
widget is ever touched off the main thread and no widget starts a raw thread.

Error handling stays generic: failures are delivered to ``on_err`` as a
:class:`BaseException`. Classifying an error into operator text is the caller's job
(see :mod:`market_monitor_gui.services.errors`).
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Final, TypeVar

_T = TypeVar("_T")

DEFAULT_MAX_WORKERS: Final[int] = 4


@dataclass(slots=True)
class _Pending:
    """A callback waiting to run on the main thread, tagged with its epoch."""

    epoch: int
    callback: Callable[[], None]


class TaskHandle:
    """Handle to a submitted task, allowing cancellation or result suppression."""

    __slots__ = ("_cancel_future", "_cancelled", "_lock", "key")

    def __init__(self, cancel_future: Callable[[], bool], key: str | None) -> None:
        self._cancel_future = cancel_future
        self._cancelled = False
        self._lock = threading.Lock()
        self.key = key

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def cancel(self) -> bool:
        """Suppress this task's result; returns whether the worker was unscheduled.

        Once cancelled, ``on_ok``/``on_err`` are never delivered even if the worker
        already started. The return value mirrors :meth:`Future.cancel`.
        """
        with self._lock:
            already = self._cancelled
            self._cancelled = True
        if already:
            return True
        return self._cancel_future()

    def _is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled


class TaskRunner:
    """Submit work to worker threads; deliver callbacks on the owning thread."""

    def __init__(self, *, max_workers: int = DEFAULT_MAX_WORKERS) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mm-task")
        self._queue: queue.SimpleQueue[_Pending] = queue.SimpleQueue()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._inflight = 0
        self._epoch = 0
        self._running: dict[str, TaskHandle] = {}
        self._closed = False

    def submit(
        self,
        fn: Callable[[], _T],
        *,
        on_ok: Callable[[_T], None],
        on_err: Callable[[BaseException], None],
        key: str | None = None,
    ) -> TaskHandle | None:
        """Run ``fn`` on a worker thread.

        Returns a :class:`TaskHandle`, or ``None`` when the runner is closed or a task
        with the same ``key`` is still pending (double-submit suppression).
        """
        with self._condition:
            if self._closed:
                return None
            if key is not None and key in self._running:
                return None
            future = self._executor.submit(fn)
            handle = TaskHandle(future.cancel, key)
            if key is not None:
                self._running[key] = handle
            epoch = self._epoch
            self._inflight += 1

        def _done(completed: Future[_T]) -> None:
            self._schedule_result(completed, handle, epoch, on_ok, on_err)
            with self._condition:
                self._inflight -= 1
                self._condition.notify_all()

        future.add_done_callback(_done)
        return handle

    def post(self, fn: Callable[[], None]) -> None:
        """Schedule ``fn`` to run on the main thread at the next :meth:`drain`."""
        with self._condition:
            if self._closed:
                return
            epoch = self._epoch
        self._queue.put(_Pending(epoch, fn))

    def drain(self) -> int:
        """Run queued callbacks on the calling (main) thread; drop stale ones.

        Returns the number of callbacks delivered.
        """
        delivered = 0
        while True:
            try:
                pending = self._queue.get_nowait()
            except queue.Empty:
                break
            if pending.epoch != self._epoch:
                continue
            pending.callback()
            delivered += 1
        return delivered

    def is_running(self, key: str) -> bool:
        """Return True while a task submitted with ``key`` has not completed."""
        with self._lock:
            return key in self._running

    def pending_count(self) -> int:
        """Number of callbacks waiting for the next :meth:`drain`."""
        return self._queue.qsize()

    def wait_idle(self, timeout: float | None = None) -> bool:
        """Block until no worker tasks are in flight; returns True if idle."""
        with self._condition:
            return self._condition.wait_for(lambda: self._inflight == 0, timeout)

    def shutdown(self, *, wait: bool = True, cancel_pending: bool = True) -> None:
        """Stop accepting work and ignore outstanding results.

        Bumping the epoch makes any callback queued after this point stale, so results
        that arrive while the window is closing are dropped by :meth:`drain`.
        """
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._epoch += 1
            running = list(self._running.values())
            self._running.clear()
        for handle in running:
            handle.cancel()
        if cancel_pending:
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
        self._executor.shutdown(wait=wait, cancel_futures=True)

    # -- internals ------------------------------------------------------------

    def _schedule_result(
        self,
        future: Future[_T],
        handle: TaskHandle,
        epoch: int,
        on_ok: Callable[[_T], None],
        on_err: Callable[[BaseException], None],
    ) -> None:
        with self._lock:
            if handle.key is not None:
                self._running.pop(handle.key, None)
            stale = handle._is_cancelled() or epoch != self._epoch
        if stale:
            return
        try:
            value = future.result()
        except CancelledError:
            return
        except BaseException as exc:  # delivered to on_err, never swallowed
            self._enqueue(epoch, handle, on_err, exc)
            return
        self._enqueue(epoch, handle, on_ok, value)

    def _enqueue(
        self,
        epoch: int,
        handle: TaskHandle,
        callback: Callable[[_T], None],
        payload: _T,
    ) -> None:
        with self._lock:
            if handle._is_cancelled() or epoch != self._epoch:
                return
        self._queue.put(_Pending(epoch, lambda: callback(payload)))
