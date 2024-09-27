import time
import asyncio
from typing import Any
from typing import Dict
import rich


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
        try:
            protocol_name = parsed_data.get("protocol")
            protocol_data = parsed_data.get("data")
            if protocol_name is None or protocol_data is None:
                rich.print("protocol_handler: Invalid protocol name or data")
                return
            if protocol_name not in self.protocols:
                rich.print("protocol_handler: Invalid protocol name")
                return

            proto = self.protocols[protocol_name]
            response = await proto.handle(protocol_data, self.node_id)
            if response is not None:
                async with send_lock:
                    await self.websocket.send(response)
        finally:
            time_taken = (time.time() * 1000) - start_time
            rich.print(
                f"protocol_handler: Time taken to process request: {time_taken}ms"
            )
