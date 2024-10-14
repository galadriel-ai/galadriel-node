import pytest
from unittest.mock import AsyncMock, patch, call

from galadriel_node.config import config
from galadriel_node.cli.node import (
    run_node,
    run_llm,
    retry_connection,
    BACKOFF_MIN,
    BACKOFF_INCREMENT,
    BACKOFF_MAX,
    ConnectionResult,
    SdkError,
)
from galadriel_node.llm_backends.vllm import LLM_BASE_URL


async def test_retry_connection_with_exceptions():
    async def connect_and_process_side_effect(*args, **kwargs):
        if connect_and_process_side_effect.call_count < 5:
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

            assert mock_connect_and_process.call_count == 6

            expected_backoff_times = [BACKOFF_MIN]
            backoff_time = BACKOFF_MIN
            for attempt in range(1, 5):
                backoff_time = min(
                    BACKOFF_MIN + (BACKOFF_INCREMENT * (2 ** (attempt - 1))),
                    BACKOFF_MAX,
                )
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


async def test_run_vllm_when_vllm_installed_and_not_running():
    model_id = "mock_model_id"
    debug = False
    process_pid = 12345
    with patch(
        "galadriel_node.llm_backends.vllm.is_installed", return_value=True
    ), patch("galadriel_node.llm_backends.vllm.is_running", return_value=False), patch(
        "galadriel_node.llm_backends.vllm.start", return_value=process_pid
    ) as mock_start, patch(
        "galadriel_node.llm_backends.vllm.is_process_running", return_value=True
    ), patch(
        "galadriel_node.cli.node.check_llm", new_callable=AsyncMock
    ) as mock_check_llm, patch(
        "galadriel_node.cli.node.llm_http_check", new_callable=AsyncMock
    ) as mock_llm_http_check:

        mock_check_llm.return_value = True
        mock_llm_http_check.return_value.ok = True

        result = await run_llm(model_id, debug)

        assert result == process_pid
        mock_start.assert_called_once()
        mock_check_llm.assert_called_once_with(LLM_BASE_URL, model_id)
        mock_llm_http_check.assert_called_once()


async def test_run_vllm_when_vllm_not_installedl():
    model_id = "mock_model_id"
    debug = False

    with patch("galadriel_node.llm_backends.vllm.is_installed", return_value=False):
        with pytest.raises(SdkError, match="vLLM is not installed"):
            await run_llm(model_id, debug)


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
            await run_llm(model_id, debug)


async def test_run_node_with_llm_base_url():
    api_url = "mock_api_url"
    rpc_url = "mock_rpc_url"
    api_key = "mock_api_key"
    node_id = "mock_node_id"
    llm_base_url = "mock_llm_base_url"
    debug = False

    with patch(
        "galadriel_node.cli.node.check_llm", new_callable=AsyncMock
    ) as mock_check_llm, patch(
        "galadriel_node.cli.node.report_hardware", new_callable=AsyncMock
    ) as mock_report_hardware, patch(
        "galadriel_node.cli.node.report_performance", new_callable=AsyncMock
    ) as mock_report_performance, patch(
        "galadriel_node.cli.node.retry_connection", new_callable=AsyncMock
    ) as mock_retry_connection, patch(
        "galadriel_node.cli.node.version_aware_get", new_callable=AsyncMock
    ), patch(
        "galadriel_node.cli.node.run_llm", new_callable=AsyncMock
    ) as mock_run_llm:
        mock_check_llm.return_value = True

        await run_node(api_url, rpc_url, api_key, node_id, llm_base_url, debug)

        mock_check_llm.assert_called_once_with(llm_base_url, config.GALADRIEL_MODEL_ID)

        assert mock_report_hardware.called
        assert mock_report_performance.called
        assert mock_retry_connection.called
        mock_run_llm.assert_not_called()


async def test_run_node_without_llm_base_url():
    api_url = "mock_api_url"
    rpc_url = "mock_rpc_url"
    api_key = "mock_api_key"
    node_id = "mock_node_id"
    llm_base_url = None
    debug = False
    process_pid = 12345

    with patch(
        "galadriel_node.cli.node.run_llm", new_callable=AsyncMock
    ) as mock_run_llm, patch(
        "galadriel_node.cli.node.report_hardware", new_callable=AsyncMock
    ) as mock_report_hardware, patch(
        "galadriel_node.cli.node.report_performance", new_callable=AsyncMock
    ) as mock_report_performance, patch(
        "galadriel_node.cli.node.retry_connection", new_callable=AsyncMock
    ) as mock_retry_connection, patch(
        "galadriel_node.cli.node.version_aware_get", new_callable=AsyncMock
    ):
        mock_run_llm.return_value = process_pid

        await run_node(api_url, rpc_url, api_key, node_id, llm_base_url, debug)

        mock_run_llm.assert_called_once_with(config.GALADRIEL_MODEL_ID, debug)

        assert mock_report_hardware.called
        assert mock_report_performance.called
        assert mock_retry_connection.called


async def test_run_node_with_llm_base_url_check_fails():
    api_url = "mock_api_url"
    rpc_url = "mock_rpc_url"
    api_key = "mock_api_key"
    node_id = "mock_node_id"
    llm_base_url = "mock_llm_base_url"
    debug = False

    with patch(
        "galadriel_node.cli.node.check_llm", new_callable=AsyncMock
    ) as mock_check_llm, patch(
        "galadriel_node.cli.node.version_aware_get", new_callable=AsyncMock
    ):
        mock_check_llm.return_value = False

        with pytest.raises(SdkError, match="LLM check failed"):
            await run_node(api_url, rpc_url, api_key, node_id, llm_base_url, debug)

        mock_check_llm.assert_called_once_with(llm_base_url, config.GALADRIEL_MODEL_ID)
