import asyncio
import time

import pytest

from passage_pipeline._rate_limit import AsyncRateLimiter


class TestAsyncRateLimiter:
    @pytest.mark.asyncio
    async def test_enforces_minimum_interval(self):
        limiter = AsyncRateLimiter(max_per_second=100)  # 10ms interval
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        # 5 calls at 100 RPS → 4 intervals of 10ms = 40ms minimum
        assert elapsed >= 0.035  # allow small timing slack

    @pytest.mark.asyncio
    async def test_first_call_is_immediate(self):
        limiter = AsyncRateLimiter(max_per_second=10)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05

    @pytest.mark.asyncio
    async def test_concurrent_callers_are_serialized(self):
        limiter = AsyncRateLimiter(max_per_second=100)  # 10ms interval
        timestamps: list[float] = []

        async def caller():
            await limiter.acquire()
            timestamps.append(time.monotonic())

        await asyncio.gather(*[caller() for _ in range(5)])
        assert len(timestamps) == 5
        # Check intervals between consecutive calls
        for i in range(1, len(timestamps)):
            assert timestamps[i] - timestamps[i - 1] >= 0.008  # ~10ms with slack
