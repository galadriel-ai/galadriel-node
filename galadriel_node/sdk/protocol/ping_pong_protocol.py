import time
from typing import Any

import rich
import asyncio

from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocket

from galadriel_node.sdk.protocol.entities import PingRequest, PongResponse, PingPongMessageType
from galadriel_node.sdk.protocol import protocol_settings

class PingPongProtocol:
    def __init__(self):
        self.rtt = 0
        self.ping_streak = 0
        self.miss_streak = 0
        rich.print(f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Protocol initialized")

    # Handle the responses from the client
    async def handle(self, data: Any, my_node_id: str, send_lock: asyncio.Lock, websocket: WebSocket):
        ping_request = PingRequest.model_validate(data)
        print("ping_request", ping_request)
        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received ping request for {ping_request.node_id}, nonce: {ping_request.nonce}")
        start_time = time.time() * 1000

        # check the version compatibility
        if ping_request.protocol_version != protocol_settings.PING_PONG_PROTOCOL_VERSION:
            rich.print(
                f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received ping with invalid protocol version from node {ping_request.node_id}"
            )
            return

        # check if we have indeed received  PING message
        if ping_request.message_type != PingPongMessageType.PING:
            rich.print(
                f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Received message other than ping from node {ping_request.node_id}"
            )
            return

        # check if the ping is for the expected node
        if my_node_id != ping_request.node_id:
            rich.print(
                f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Ignoring ping received for unexpected node {ping_request.node_id}"
            )
            return

        # Update the state as seen by the server
        self.rtt = ping_request.rtt
        self.ping_streak = ping_request.ping_streak
        self.miss_streak = ping_request.miss_streak

        # Construct the pong response
        pong_response = PongResponse(
            node_id=ping_request.node_id,  # use the received node_id
            message_type=PingPongMessageType.PONG,
            nonce=ping_request.nonce,  # use the received nonce
        )

        # Send it to the server
        data = jsonable_encoder(pong_response)
        message = {"protocol": protocol_settings.PING_PONG_PROTOCOL_NAME, "data": data}
        async with send_lock:
            await websocket.send(message)
        time_taken = (time.time() * 1000) - start_time
        rich.print(
            f"{protocol_settings.PING_PONG_PROTOCOL_NAME}: Sent pong response in {time_taken} msec, nonce: {pong_response.nonce}, rtt: {self.rtt}, ping_streak: {self.ping_streak}, miss_streak: {self.miss_streak}")
