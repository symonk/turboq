import asyncio

import pytest
from assertpy import assert_that

from turboq import PoolStartedError
from turboq import PriorityTask
from turboq import WorkerPool


def coro_factory():
    async def coro(*args, **kwargs):
        await asyncio.sleep(0.1)
        print(*args, **kwargs)
        return 100

    return coro


@pytest.mark.asyncio
async def test_starting_already_started_pool_errors() -> None:
    p = WorkerPool(max_workers=1)
    p.start()
    with pytest.raises(
        PoolStartedError, match="pool is already running, cannot be started twice"
    ):
        p.start()


@pytest.mark.asyncio
async def test_task_submission() -> None:
    async with WorkerPool(max_workers=1) as p:
        t = PriorityTask(
            priority=0, coro_factory=coro_factory, coro_args=(), coro_kwargs={}
        )
        await p.submit(t)
        done = await t
        assert_that(done).is_equal_to(100)


@pytest.mark.asyncio
async def test_many_tasks() -> None:
    p = WorkerPool(max_workers=100)
    p.start()
    tees = []
    for _ in range(1000):
        tee = await p.submit(
            PriorityTask(
                priority=0, coro_factory=coro_factory, coro_args=(), coro_kwargs={}
            )
        )
        tees.append(tee)
    await p.stop()
    out = await asyncio.gather(*tees)
    assert_that(out).contains_only(100)
