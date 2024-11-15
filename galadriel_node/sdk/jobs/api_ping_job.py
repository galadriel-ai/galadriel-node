import asyncio
from logging import getLogger
from typing import Optional

from ping3 import ping

from galadriel_node.config import config

logger = getLogger()


class ApiPingJob:
    def __init__(self, domain: str) -> None:
        self.domain = domain
        self.ping_time: list[Optional[int]] = []
        self._lock = asyncio.Lock()

    async def run(self):
        while True:
            try:
                await asyncio.sleep(config.GALADRIEL_API_PING_INTERVAL)
                ping_time = self._check_api_ping_time()
                await self._append_ping_time(ping_time)
            except Exception as _:
                await self._append_ping_time(None)
                logger.error("Error occurs in API ping job.", exc_info=True)

    def _check_api_ping_time(self) -> Optional[int]:
        ping_time = ping(self.domain, unit="ms")
        logger.debug(f"Ping to domain: {self.domain}")
        if not ping_time:
            logger.info("Failed to ping the Galadriel API.")
            return None
        logger.debug(f"API ping time: {ping_time}ms")
        return int(ping_time)

    async def _append_ping_time(self, ping_time: Optional[int]):
        async with self._lock:
            self.ping_time.append(ping_time)

    async def get_and_clear_ping_time(self) -> list[Optional[int]]:
        async with self._lock:
            ping_time = self.ping_time
            self.ping_time = []
        return ping_time
