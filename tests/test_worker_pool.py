import pytest
from turboq import WorkerPool
from turboq import PoolStartedError
import asyncio

@pytest.mark.asyncio
async def test_starting_already_started_pool_errors() -> None:
    p = WorkerPool(max_workers=1)
    p.start()
    with pytest.raises(PoolStartedError, match="pool is already running, cannot be started twice"):
        p.start()