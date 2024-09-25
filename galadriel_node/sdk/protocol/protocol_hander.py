import json
import rich
import asyncio
from typing import Any
from typing import Dict

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
        protocol_name = parsed_data.get("protocol")
        data = parsed_data.get("data")
        protocol_data = json.loads(data)
        if protocol_name is None or protocol_data is None:
            rich.print(
                f"protocol_handler: Invalid protocol name or data"
            )
            return
        if protocol_name in self.protocols:
            proto = self.protocols[protocol_name]
            await proto.handle(protocol_data, self.node_id, send_lock, self.websocket)
        else:
            rich.print(
                f"protocol_handler: Invalid protocol name {protocol_name}"
            )
