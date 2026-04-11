from __future__ import annotations

import queue
import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class DroppingWorker(Generic[T]):
    def __init__(self, name: str, handler: Callable[[T], None], log: Callable[[str], None], maxsize: int) -> None:
        self._name = name
        self._handler = handler
        self._log = log
        self._queue: queue.Queue[T] = queue.Queue(maxsize=maxsize)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()
        self._dropped_items = 0

    def submit(self, item: T) -> None:
        while True:
            try:
                self._queue.put_nowait(item)
                return
            except queue.Full:
                try:
                    self._queue.get_nowait()
                    self._dropped_items += 1
                    if self._dropped_items in {1, 10} or self._dropped_items % 50 == 0:
                        self._log(f"{self._name} queue is full; dropped {self._dropped_items} pending item(s) to keep latency low.")
                except queue.Empty:
                    return

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=1.5)
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._handler(item)
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self._log(f"{self._name} worker error: {exc}")
