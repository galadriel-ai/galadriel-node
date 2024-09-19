import pytest
from unittest.mock import AsyncMock, patch, call

from galadriel_node.cli.node import (
    retry_connection,
    BACKOFF_MIN,
    BACKOFF_MAX,
    ConnectionResult,
)


async def test_retry_connection_with_exceptions():
    async def connect_and_process_side_effect(*args, **kwargs):
        if connect_and_process_side_effect.call_count < 3:
            connect_and_process_side_effect.call_count += 1
            raise Exception("Mock exception")
        else:
            # don't retry anymore
            return ConnectionResult(retry=False)

    connect_and_process_side_effect.call_count = 0

    with patch(
        "galadriel_node.cli.node.connect_and_process", new_callable=AsyncMock
    ) as mock_connect_and_process:
        mock_connect_and_process.side_effect = connect_and_process_side_effect

        with patch(
            "galadriel_node.cli.node.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await retry_connection(
                "mock_rpc_url",
                "mock_api_key",
                "mock_node_id",
                "mock_llm_base_url",
                False,
            )

            assert mock_connect_and_process.call_count == 4

            expected_backoff_times = [BACKOFF_MIN]
            backoff_time = BACKOFF_MIN
            for _ in range(2):
                backoff_time = min(backoff_time * 2, BACKOFF_MAX)
                expected_backoff_times.append(backoff_time)

            expected_sleep_calls = [call(time) for time in expected_backoff_times]

            assert mock_sleep.await_args_list == expected_sleep_calls


async def test_retry_connection_keyboard_interrupt():
    async def connect_and_process_side_effect(*args, **kwargs):
        raise KeyboardInterrupt()

    with patch(
        "galadriel_node.cli.node.connect_and_process", new_callable=AsyncMock
    ) as mock_connect_and_process:
        mock_connect_and_process.side_effect = connect_and_process_side_effect

        with pytest.raises(KeyboardInterrupt):
            await retry_connection(
                "mock_rpc_url",
                "mock_api_key",
                "mock_node_id",
                "mock_llm_base_url",
                False,
            )

        assert mock_connect_and_process.await_count == 1
