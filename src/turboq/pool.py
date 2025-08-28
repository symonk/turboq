from __future__ import annotations

import asyncio
import typing

from .exception import PoolStartedError
from .task import PriorityTask
from .worker import Worker


class WorkerPool:
    """Workerpool is an implementation of the Pool interface that enables
    dispatching various tasks asynchronously, backed by `asyncio`.

    The pool itself does not start a loop, client code is responsible for managing
    the loop.

    The internals of the WorkerPool utilise a PriorityQueue, where the lower the
    priority, the sooner it will be picked up by a worker.

    Note: WorkerPool objects are not thread safe.
    """

    def __init__(self, max_workers: int, worker_batch_size: int = 1) -> None:
        self.max_workers = max(0, max_workers)
        self.worker_batch_size = worker_batch_size
        self.q = asyncio.PriorityQueue[PriorityTask](maxsize=0)
        self._shutdown_alert = asyncio.Event()
        self._started = False
        self._worker_tasks: list[asyncio.Task] = []

    def start(self) -> None:
        """start starts the worker pool, creating upto max_workers number of
        tasks monitoring the internal queue."""
        if self._started:
            raise PoolStartedError("pool is already running, cannot be started twice")
        self._started = True
        for worker_id in range(self.max_workers):
            w = Worker(identity=worker_id, q=self.q, stopper=self._shutdown_alert)
            worker_task = asyncio.create_task(w())
            self._worker_tasks.append(worker_task)
            print("started worker: ", worker_id)

    async def submit(self, t: PriorityTask) -> PriorityTask:
        """submit enqueues a new task onto the pool, to be scheduled
        for execution at some point in the future.  submit is non
        blocking."""
        await self.q.put(t)
        return t

    async def submit_wait(self, t: PriorityTask) -> None:
        """submit enqueues a new task onto the pool and blocks until
        that particular task has been completed."""

    async def stop(self, graceful: bool = True) -> None:
        """stop attempts to terminate the workerpool.
        If graceful is set, stop will block until all inflight
        tasks are completed and the internal queues are emptied.
        Attempting to submit new tasks after stops has been called
        will raise an exception.
        """
        self._shutdown_alert.set()
        await self.q.join()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

    async def drain(self) -> None:
        """drain blocks enqueued tasks until the current internal
        queues are emptied.  Upon emptying the queue normal consumption
        will resume."""

    async def throttle(self, predicate: typing.Callable[[None, None], bool]) -> None:
        """throttle puts a temporary pause on the workers, preventing
        them from executing tasks until the predicate is true."""

    async def __aenter__(self) -> WorkerPool:
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
