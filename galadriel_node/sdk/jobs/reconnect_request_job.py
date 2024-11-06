import asyncio

from galadriel_node.config import config
from galadriel_node.sdk.jobs.inference_status_counter import InferenceStatusCounter
from galadriel_node.sdk.protocol.ping_pong_protocol import PingPongProtocol


async def wait_for_reconnect(
    inference_status_counter: InferenceStatusCounter,
    ping_pong_protocol: PingPongProtocol,
) -> bool:
    while True:
        await asyncio.sleep(config.RECONNECT_JOB_INTERVAL)

        is_free = await inference_status_counter.is_free()
        reconnect_requested = await ping_pong_protocol.get_reconnect_requested()

        if is_free and reconnect_requested:
            return True
