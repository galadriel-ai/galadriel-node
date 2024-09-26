import json
from typing import Any

import rich

from fastapi.encoders import jsonable_encoder

from galadriel_node.sdk.protocol.entities import (
    PingRequest,
    PongResponse,
    PingPongMessageType,
)
from galadriel_node.sdk.protocol import protocol_settings


# pylint: disable=too-few-public-methods,
class PingPongProtocol:
    def __init__(self):
        self.rtt = 0
        self.ping_streak = 0
        self.miss_streak = 0
        rich.print(f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Protocol initialized")

    # Handle the responses from the client
    async def handle(self, data: Any, my_node_id: str) -> str | None:
        print(data)
        # TODO: we should replace these mess with direct pydantic model objects once the
        # inference is inside the protocol. Until then, we will use the dict objects and manually
        # validate them.
        ping_request = _extract_and_validate(data)
        if ping_request is None:
            rich.print(
                f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Invalid data received: {data}"
            )
            return

        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received ping request for {ping_request.node_id}, "
            f"nonce: {ping_request.nonce}"
        )

        # Protocol checks
        if _protocol_validations(my_node_id, ping_request) is False:
            return

        # Update the state as seen by the server
        self.rtt = ping_request.rtt
        self.ping_streak = ping_request.ping_streak
        self.miss_streak = ping_request.miss_streak

        # Construct the pong response
        pong_response = PongResponse(
            protocol_version=protocol_settings.PING_PONG_PROTOCOL_VERSION,
            message_type=PingPongMessageType.PONG,
            node_id=ping_request.node_id,  # use the received node_id
            nonce=ping_request.nonce,  # use the received nonce
        )

        # Send it to the server
        data = jsonable_encoder(pong_response)
        pong_message = json.dumps(
            {"protocol": protocol_settings.PING_PONG_PROTOCOL_NAME, "data": data}
        )
        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Sent pong , "
            f"nonce: {pong_response.nonce}, "
            f"rtt: {self.rtt}, "
            f"ping_streak: {self.ping_streak}, "
            f"miss_streak: {self.miss_streak}"
        )
        return pong_message


def _protocol_validations(my_node_id: str, ping_request: PingRequest) -> bool:
    # 1 - check if the ping is for the expected node
    if my_node_id != ping_request.node_id:
        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Ignoring ping received for unexpected node "
            f"{ping_request.node_id}"
        )
        return False

    # 2 - check if we have indeed received PING message
    if ping_request.message_type != PingPongMessageType.PING:
        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received message other than ping from node "
            f"{ping_request.node_id}, {ping_request.message_type}, {PingPongMessageType.PING}"
        )
        return False

    # 3 - check the version compatibility
    if ping_request.protocol_version != protocol_settings.PING_PONG_PROTOCOL_VERSION:
        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received ping with invalid protocol version from node "
            f"{ping_request.node_id}"
        )
        return False
    return True


# pylint: disable=too-many-boolean-expressions
def _extract_and_validate(data: Any) -> PingRequest | None:
    ping_request = PingRequest(
        protocol_version="",
        message_type=1,
        node_id="",
        nonce="",
        rtt=0,
        ping_streak=0,
        miss_streak=0,
    )
    if "protocol_version" in data:
        ping_request.protocol_version = data["protocol_version"]
    if "message_type" in data:
        message_type = data["message_type"]
        try:
            ping_request.message_type = PingPongMessageType(message_type)
        except KeyError:
            ping_request.message_type = None
    if "node_id" in data:
        ping_request.node_id = data["node_id"]
    if "nonce" in data:
        ping_request.nonce = data["nonce"]
    if "rtt" in data:
        ping_request.rtt = data["rtt"]
    if "ping_streak" in data:
        ping_request.ping_streak = data["ping_streak"]
    if "miss_streak" in data:
        ping_request.miss_streak = data["miss_streak"]
    if (
        ping_request.protocol_version is None
        or ping_request.message_type is None
        or ping_request.node_id is None
        or ping_request.nonce is None
        or ping_request.rtt is None
        or ping_request.ping_streak is None
        or ping_request.miss_streak is None
    ):
        return None
    return ping_request
