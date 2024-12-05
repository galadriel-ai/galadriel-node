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
from galadriel_node.sdk.util.inference_status_counter import LockedCounter

logger = get_node_logger()


# pylint: disable=too-few-public-methods,
def validate_request(data: Any) -> Optional[ImageGenerationWebsocketRequest]:
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


class ImageGeneration:

    def __init__(self, model: str):
        self.counter = LockedCounter()
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
        generation_response = None
        try:
            images = self.pipeline.generate_images(
                request.prompt,
                request.image,
                request.n,
            )
            generation_response = ImageGenerationWebsocketResponse(
                request_id=request.request_id,
                images=images,
                error=None,
            )
        except Exception as e:
            logger.error(f"Errors during image generation: {e}")
            generation_response = ImageGenerationWebsocketResponse(
                request_id=request.request_id,
                images=[],
                error=str(e),
            )

        # Send the response to the client
        response_data = jsonable_encoder(generation_response)
        encoded_response_data = json.dumps(response_data)
        logger.info(f"Sent image generation response for request {request.request_id}")

        try:
            await self.counter.increment()
            logger.debug(f"Response data: {response_data}")
            async with send_lock:
                await websocket.send(encoded_response_data)
            logger.debug(f"REQUEST {request.request_id} END")
        except Exception as e:
            logger.error(
                f"Failed to send response for request {request.request_id}: {e}"
            )
        finally:
            await self.counter.decrement()
        return

    async def is_idle(self) -> bool:
        return await self.counter.is_zero()
