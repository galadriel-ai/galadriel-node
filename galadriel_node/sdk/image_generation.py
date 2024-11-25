import asyncio
import json
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from websockets import WebSocketClientProtocol

from galadriel_node.sdk.logging_utils import get_node_logger
from galadriel_node.sdk.protocol.entities import (
    ImageGenerationWebsocketRequest,
    ImageGenerationWebsocketResponse,
)
from galadriel_node.sdk.diffusers import Diffusers

logger = get_node_logger()


# pylint: disable=too-few-public-methods,
class ImageGeneration:

    def __init__(self, model: str):
        self.counter = 0
        self.lock = asyncio.Lock()
        self.pipeline = Diffusers(model)
        logger.info("ImageGeneration engine initialized")

    async def process_request(
        self,
        request: ImageGenerationWebsocketRequest,
        websocket: WebSocketClientProtocol,
        send_lock: asyncio.Lock,
    ) -> None:

        logger.info(
            f"Received image generation request. Request Id: {request.request_id}"
        )

        # Generate the image
        images = self.pipeline.generate_images(
            request.prompt,
            request.image,
            request.n,
        )

        # Send the response to the client
        generation_response = ImageGenerationWebsocketResponse(
            request_id=request.request_id,
            images=images,
        )

        response_data = jsonable_encoder(generation_response)
        encoded_response_data = json.dumps(response_data)
        logger.info(f"Sent image generation response for request {request.request_id}")

        try:
            async with self.lock:
                self.counter += 1
            logger.debug(f"Response data: {response_data}")
            async with send_lock:
                await websocket.send(encoded_response_data)
            logger.debug(f"REQUEST {request.request_id} END")
        except Exception as e:
            logger.error(
                f"Failed to send response for request {request.request_id}: {e}"
            )
        finally:
            async with self.lock:
                if self.counter > 0:
                    self.counter -= 1
        return

    def validate_request(self, data: Any) -> Optional[ImageGenerationWebsocketRequest]:
        try:
            image_generation_request = ImageGenerationWebsocketRequest(
                request_id=data.get("request_id"),
                prompt=data.get("prompt"),
                image=data.get("image"),
                n=data.get("n"),
                size=data.get("size"),
            )
            return image_generation_request
        except Exception:
            return None

    async def is_idle(self) -> bool:
        async with self.lock:
            return self.counter == 0
