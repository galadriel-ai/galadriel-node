from unittest.mock import AsyncMock, patch

import pytest

from galadriel_node.sdk.jobs.reconnect_request_job import wait_for_reconnect


@pytest.mark.asyncio
async def test_wait_for_reconnect():
    inference_status_counter = AsyncMock()
    ping_pong_protocol = AsyncMock()
    ping_pong_protocol.get_reconnect_requested.return_value = AsyncMock(
        return_value=True
    )
    inference_status_counter.is_free.return_value = AsyncMock(return_value=True)

    with patch(
        "galadriel_node.sdk.jobs.reconnect_request_job.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        res = await wait_for_reconnect(inference_status_counter, ping_pong_protocol)
    assert res == True
