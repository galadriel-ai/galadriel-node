import asyncio
from typing import Optional

from galadriel_node.config import config
from galadriel_node.sdk.image_generation import ImageGeneration
from galadriel_node.sdk.util.inference_status_counter import LockedCounter
from galadriel_node.sdk.protocol.ping_pong_protocol import PingPongProtocol


async def wait_for_reconnect(
    inference_status_counter: LockedCounter,
    image_generation_engine: Optional[ImageGeneration],
    ping_pong_protocol: PingPongProtocol,
) -> bool:
    while True:
        await asyncio.sleep(config.RECONNECT_JOB_INTERVAL)

        no_pending_llm_inference_requests = await inference_status_counter.is_zero()
        reconnect_requested = await ping_pong_protocol.get_reconnect_requested()
        # If image generation engine is not None, check if it is idle
        no_pending_image_generation_requests = True
        if image_generation_engine is not None:
            no_pending_image_generation_requests = (
                await image_generation_engine.no_pending_requests()
            )

        if (
            reconnect_requested
            and no_pending_llm_inference_requests
            and no_pending_image_generation_requests
        ):
            return True
