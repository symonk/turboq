import asyncio
import typing

from .task import PriorityTask


class Worker:
    """Worker encapsulates a coroutine that can receive tasks to execute."""

    def __init__(
        self,
        identity: int,
        q: asyncio.PriorityQueue[PriorityTask],
        stopper: asyncio.Event,
    ) -> None:
        self.identity = identity
        self.q = q
        self.stopper = stopper
        self.stopped = False

    async def __call__(self) -> typing.Coroutine:
        # TODO: These workers can crash and the event loop will still carry on, except the queue
        # will be completely blocking!
        # TODO: asyncio.CancelledError handling, shielding etc.
        while True:
            if self.stopper.is_set() and self.q.empty():
                break
            try:
                # avoid blocking indefinitely on queue.get() because we want to be frequently
                # checking the asyncio.Event for shutdown.
                task: PriorityTask = await asyncio.wait_for(self.q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print("got exeption getting worker task: ", e)
                raise
            try:
                await task.run()
            except Exception as e:
                print("got exception executing worker task: ", e)
                raise
            finally:
                self.q.task_done()
