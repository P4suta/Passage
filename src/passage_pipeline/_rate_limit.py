import asyncio
import time


class AsyncRateLimiter:
    """Fixed-interval rate limiter for async contexts.

    Ensures a minimum interval between requests by serializing access
    through an asyncio lock.
    """

    def __init__(self, max_per_second: float) -> None:
        self._interval = 1.0 / max_per_second
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._last_call + self._interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
