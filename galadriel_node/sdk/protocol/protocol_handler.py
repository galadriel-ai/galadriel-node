import asyncio
import time
from logging import getLogger
from typing import Any
from typing import Dict

logger = getLogger()


# Handler for all the protocols
class ProtocolHandler:
    def __init__(self, node_id: str, websocket: Any):
        self.node_id = node_id
        self.websocket = websocket
        self.protocols: Dict[str, Any] = {}

    def register(self, protocol_name: str, protocol: Any):
        self.protocols[protocol_name] = protocol

    def deregister(self, protocol_name: str):
        if protocol_name in self.protocols:
            del self.protocols[protocol_name]

    def get(self, protocol_name: str) -> Any:
        return self.protocols.get(protocol_name)

    async def handle(self, parsed_data: Any, send_lock: asyncio.Lock):
        # see how much time we take to process this request
        start_time = time.time() * 1000
        protocol_name = parsed_data.get("protocol")
        protocol_data = parsed_data.get("data")
        if protocol_name is None:
            logger.error("protocol_handler: protocol name is None")
            return

        if protocol_data is None:
            logger.error("protocol_handler: protocol data is None")
            return

        protocol = self.protocols.get(protocol_name)
        if protocol is None:
            logger.error(f"protocol_handler: Invalid protocol name {protocol_name}")
            return

        logger.error(f"protocol_handler: Handle protocol {protocol_name}")
        try:
            response = await protocol.handle(protocol_data, self.node_id)
            if response is not None:
                async with send_lock:
                    await self.websocket.send(response)
        finally:
            time_taken = (time.time() * 1000) - start_time
            logger.info(
                f"protocol_handler: protocol {protocol_name} took {time_taken}ms to process request"
            )
