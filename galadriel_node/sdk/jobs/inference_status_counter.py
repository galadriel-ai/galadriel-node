import asyncio


class InferenceStatusCounter:
    def __init__(self):
        self._counter = 0
        self._lock = asyncio.Lock()

    async def increment(self):
        async with self._lock:
            self._counter += 1

    async def decrement(self):
        async with self._lock:
            if self._counter > 0:
                self._counter -= 1

    async def is_zero(self) -> bool:
        async with self._lock:
            return self._counter == 0
