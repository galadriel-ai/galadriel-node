import pytest
from unittest.mock import AsyncMock, patch, call

from galadriel_node.cli.node import (
    run_llm,
    retry_connection,
    BACKOFF_MIN,
    BACKOFF_MAX,
    ConnectionResult,
    SdkError,
)
from galadriel_node.llm_backends.vllm import LLM_BASE_URL


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


async def test_run_vllm_when_llm_base_url_is_provided():
    llm_base_url = "http://mock-llm-url.com"
    model_id = "mock_model_id"
    debug = False

    with patch(
        "galadriel_node.cli.node.check_llm", new_callable=AsyncMock
    ) as mock_check_llm, patch(
        "galadriel_node.llm_backends.vllm.is_installed", return_value=True
    ) as mock_is_installed:
        mock_check_llm.return_value = True

        result = await run_llm(llm_base_url, model_id, debug)

        assert result == llm_base_url
        mock_check_llm.assert_called_once_with(llm_base_url, model_id)
        mock_is_installed.assert_not_called()


async def test_run_vllm_when_vllm_installed_and_running():
    model_id = "mock_model_id"
    debug = False

    with patch(
        "galadriel_node.llm_backends.vllm.is_installed", return_value=True
    ), patch("galadriel_node.llm_backends.vllm.is_running", return_value=True), patch(
        "galadriel_node.cli.node.check_llm", new_callable=AsyncMock
    ) as mock_check_llm, patch(
        "galadriel_node.llm_backends.vllm.start", return_value=12345
    ) as mock_start:

        mock_check_llm.return_value = True

        result = await run_llm(None, model_id, debug)

        assert result == LLM_BASE_URL
        mock_check_llm.assert_called_once_with(LLM_BASE_URL, model_id)
        mock_start.assert_not_called()


async def test_run_vllm_when_vllm_installed_and_not_running():
    model_id = "mock_model_id"
    debug = False

    with patch(
        "galadriel_node.llm_backends.vllm.is_installed", return_value=True
    ), patch("galadriel_node.llm_backends.vllm.is_running", return_value=False), patch(
        "galadriel_node.llm_backends.vllm.start", return_value=12345
    ) as mock_start, patch(
        "galadriel_node.llm_backends.vllm.is_process_running", return_value=True
    ), patch(
        "galadriel_node.cli.node.check_llm", new_callable=AsyncMock
    ) as mock_check_llm, patch(
        "galadriel_node.cli.node.llm_http_check", new_callable=AsyncMock
    ) as mock_llm_http_check:

        mock_check_llm.return_value = True
        mock_llm_http_check.return_value.ok = True

        result = await run_llm(None, model_id, debug)

        assert result == LLM_BASE_URL
        mock_start.assert_called_once()
        mock_check_llm.assert_called_once_with(LLM_BASE_URL, model_id)
        mock_llm_http_check.assert_called_once()


async def test_run_vllm_when_vllm_not_installed_and_no_llm_base_url():
    model_id = "mock_model_id"
    debug = False

    with patch("galadriel_node.llm_backends.vllm.is_installed", return_value=False):
        with pytest.raises(SdkError, match="vLLM is not installed"):
            await run_llm(None, model_id, debug)


async def test_run_vllm_when_vllm_process_dies():
    model_id = "mock_model_id"
    debug = False

    with patch(
        "galadriel_node.llm_backends.vllm.is_installed", return_value=True
    ), patch("galadriel_node.llm_backends.vllm.is_running", return_value=False), patch(
        "galadriel_node.llm_backends.vllm.start", return_value=12345
    ), patch(
        "galadriel_node.llm_backends.vllm.is_process_running", side_effect=[True, False]
    ), patch(
        "galadriel_node.cli.node.llm_http_check", new_callable=AsyncMock
    ) as mock_llm_http_check:

        mock_llm_http_check.return_value.ok = False

        with pytest.raises(
            SdkError, match=r"vLLM process \(PID: 12345\) died unexpectedly"
        ):
            await run_llm(None, model_id, debug)
