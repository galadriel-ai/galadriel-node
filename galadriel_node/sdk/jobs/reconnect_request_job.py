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

        is_zero = await inference_status_counter.is_zero()
        reconnect_requested = await ping_pong_protocol.get_reconnect_requested()
        # If image generation engine is not None, check if it is idle
        is_idle = True
        if image_generation_engine is not None:
            is_idle = await image_generation_engine.is_idle()

        if is_zero and is_idle and reconnect_requested:
            return True
