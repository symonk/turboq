from __future__ import annotations

import asyncio
import typing


class PriorityTask:
    """PriorityTask encapsulates are similar to future like objects, except
    they offer more robust functionality.  The WorkerPool requires
    these PoolTasks on submission, but they can be awaited just like
    any other future like object.

    Awaiting the same coroutines multiple times (in the retry) case will raise
    a runtime error, clients creating a task should provide a factory function
    that when given the *args and **kwargs will yield the `Coroutine` that should
    be executed.
    """

    def __init__(
        self,
        *,
        priority: int,
        coro_factory: typing.Callable[..., typing.Awaitable],
        retries: int = 0,
        retry_backoff: int = 0,
        coro_args: tuple[typing.Any] = (),
        coro_kwargs: dict[typing.Any, typing.Any] = None,
    ) -> None:
        self.priority = priority
        self._coro_factory = coro_factory
        self.retries = retries
        self.retry_backoff = retry_backoff
        self._future: asyncio.Future = asyncio.Future()
        self._coro_args = coro_args
        self._coro_kwargs = coro_kwargs or {}

    def __await__(self) -> ...:
        return self._future.__await__()

    async def run(self):
        """run handles executing the actual priority task and aligning the
        internal future with it's results and exceptions.

        retriability is handled by the task itself, rather than the worker pool.
        """
        attempt = 0
        while attempt <= self.retries:
            try:
                coro = self._coro_factory()(*self._coro_args, **self._coro_kwargs)
                result = await coro
                self._future.set_result(result)
                return result
            except Exception as e:
                attempt += 1
                if attempt > self.retries:
                    self._future.set_exception(e)
                    raise
            await asyncio.sleep(self.retry_backoff * (2 ** (attempt - 1)))

    def __lt__(self, other: PriorityTask) -> bool:
        return self.priority < other.priority
