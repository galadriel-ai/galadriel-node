import asyncio
import json
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder

from galadriel_node.sdk.jobs.api_ping_job import ApiPingJob
from galadriel_node.sdk.logging_utils import get_node_logger
from galadriel_node.sdk.protocol import protocol_settings
from galadriel_node.sdk.protocol.entities import (
    PingRequest,
    PongResponse,
    PingPongMessageType,
    NodeReconnectRequest,
)

logger = get_node_logger()


# pylint: disable=too-few-public-methods,
class PingPongProtocol:

    def __init__(self, api_ping_job: ApiPingJob):
        self.rtt = 0
        self.ping_streak = 0
        self.miss_streak = 0
        self.api_ping_job = api_ping_job
        self.reconnect_requested = False
        self._lock = asyncio.Lock()
        logger.info(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Protocol initialized"
        )

    # Handle the responses from the client
    async def handle(self, data: Any, my_node_id: str) -> str | None:
        node_reconnect_request = _validate_reconnect_request(data)
        if (
            node_reconnect_request
            and node_reconnect_request.message_type
            == PingPongMessageType.RECONNECT_REQUEST
            and node_reconnect_request.reconnect_request
        ):
            logger.info(
                f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received reconnect request. "
                "There is a more performing server found. Trying to connect to this server."
            )
            await self.set_reconnect_requested(node_reconnect_request.reconnect_request)
            return None

        # TODO: we should replace these mess with direct pydantic model objects once the
        # inference is inside the protocol. Until then, we will use the dict objects and manually
        # validate them.
        ping_request = _extract_and_validate_ping_request(data)
        if ping_request is None:
            logger.info(
                f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Invalid data received: {data}"
            )
            return None

        logger.info(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: "
            f"Received ping request for {ping_request.node_id}, nonce: {ping_request.nonce}"
        )

        # Protocol checks
        if _protocol_validations(my_node_id, ping_request) is False:
            return None

        # Update the state as seen by the server
        self.rtt = ping_request.rtt
        self.ping_streak = ping_request.ping_streak
        self.miss_streak = ping_request.miss_streak

        api_ping_time = await self.api_ping_job.get_and_clear_ping_time()

        # Construct the pong response
        pong_response = PongResponse(
            protocol_version=protocol_settings.PING_PONG_PROTOCOL_VERSION,
            message_type=PingPongMessageType.PONG,
            node_id=ping_request.node_id,  # use the received node_id
            nonce=ping_request.nonce,  # use the received nonce
            api_ping_time=api_ping_time,
        )

        # Send it to the server
        data = jsonable_encoder(pong_response)
        pong_message = json.dumps(
            {"protocol": protocol_settings.PING_PONG_PROTOCOL_NAME, "data": data}
        )
        logger.info(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Sent pong , "
            f"nonce: {pong_response.nonce}, "
            f"rtt: {self.rtt}, "
            f"ping_streak: {self.ping_streak}, "
            f"miss_streak: {self.miss_streak}"
        )
        return pong_message

    async def set_reconnect_requested(self, reconnect_requested: bool):
        async with self._lock:
            self.reconnect_requested = reconnect_requested

    async def get_reconnect_requested(self) -> bool:
        async with self._lock:
            return self.reconnect_requested


def _protocol_validations(my_node_id: str, ping_request: PingRequest) -> bool:
    # 1 - check if the ping is for the expected node
    if my_node_id != ping_request.node_id:
        logger.info(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: "
            f"Ignoring ping received for unexpected node {ping_request.node_id}"
        )
        return False

    # 2 - check if we have indeed received PING message
    if ping_request.message_type != PingPongMessageType.PING:
        logger.info(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: "
            f"Received message other than ping from node "
            f"{ping_request.node_id}, {ping_request.message_type}, {PingPongMessageType.PING}"
        )
        return False

    # 3 - check the version compatibility
    if ping_request.protocol_version != protocol_settings.PING_PONG_PROTOCOL_VERSION:
        logger.info(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: "
            f"Received ping with invalid protocol version from node {ping_request.node_id}"
        )
        return False
    return True


# pylint: disable=too-many-boolean-expressions
def _extract_and_validate_ping_request(data: Any) -> PingRequest | None:
    ping_request = PingRequest(
        protocol_version="",
        message_type=PingPongMessageType.PING,
        node_id="",
        nonce="",
        rtt=0,
        ping_streak=0,
        miss_streak=0,
    )

    ping_request.protocol_version = data.get("protocol_version")
    message_type = data.get("message_type")
    try:
        ping_request.message_type = PingPongMessageType(message_type)
    except KeyError:
        return None
    ping_request.node_id = data.get("node_id")
    ping_request.nonce = data.get("nonce")
    ping_request.rtt = data.get("rtt")
    ping_request.ping_streak = data.get("ping_streak")
    ping_request.miss_streak = data.get("miss_streak")
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


def _validate_reconnect_request(data: Any) -> Optional[NodeReconnectRequest]:
    try:
        reconnect_request = NodeReconnectRequest(
            protocol_version=data.get("protocol_version"),
            message_type=PingPongMessageType(data.get("message_type")),
            node_id=data.get("node_id"),
            nonce=data.get("nonce"),
            reconnect_request=data.get("reconnect_request"),
        )
        return reconnect_request
    except Exception:
        return None
