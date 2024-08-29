from urllib.parse import urljoin

import openai
from unittest.mock import AsyncMock, MagicMock, patch
from galadriel_node.sdk.entities import (
    InferenceRequest,
    InferenceResponse,
    InferenceStatusCodes,
)
from galadriel_node.sdk.llm import Llm

INFERENCE_BASE_URL = "https://api.openai.com/v1"


async def test_llm_execute_successful():
    request = InferenceRequest(id="test_id", chat_request={"stream": True})

    mock_openai = AsyncMock()
    mock_create = AsyncMock()

    async def mock_aiter():
        yield {"choices": [{"delta": {"content": "chunk1"}}]}
        yield {"choices": [{"delta": {"content": "chunk2"}}]}

    mock_create.return_value = mock_aiter()
    mock_openai.chat.completions.create = mock_create

    with patch("openai.AsyncOpenAI", return_value=mock_openai):
        llm = Llm()
        results = [item async for item in llm.execute(request, INFERENCE_BASE_URL)]

        assert len(results) == 2
        assert isinstance(results[0], InferenceResponse)
        assert results[0].chunk == {"choices": [{"delta": {"content": "chunk1"}}]}
        assert results[0].error is None
        assert isinstance(results[1], InferenceResponse)
        assert results[1].chunk == {"choices": [{"delta": {"content": "chunk2"}}]}
        assert results[1].error is None


async def test_llm_execute_with_bad_request_exception():
    request = InferenceRequest(id="test_id", chat_request={"stream": True})

    with patch("openai.AsyncOpenAI") as MockOpenAI:
        response_mock = MagicMock()
        response_mock.request = MagicMock()
        response_mock.status_code = 400
        MockOpenAI.return_value.chat.completions.create.side_effect = (
            openai.BadRequestError(
                message="Inference failed", response=response_mock, body=""
            )
        )

        llm = Llm()
        results = [item async for item in llm.execute(request, INFERENCE_BASE_URL)]

        assert len(results) == 1
        assert isinstance(results[0], InferenceResponse)
        assert results[0].error is not None
        assert results[0].error.status_code == InferenceStatusCodes.BAD_REQUEST.value
        assert results[0].error.message == "Inference failed"


async def test_llm_execute_with_generic_exception():
    request = InferenceRequest(id="test_id", chat_request={"stream": True})

    with patch("openai.AsyncOpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception(
            "Inference failed"
        )

        llm = Llm()
        results = [item async for item in llm.execute(request, INFERENCE_BASE_URL)]

        assert len(results) == 1
        assert isinstance(results[0], InferenceResponse)
        assert results[0].error is not None
        assert results[0].error.status_code == InferenceStatusCodes.UNKNOWN_ERROR
        assert results[0].error.message == "Inference failed"


async def test_llm_execute_url_construction():
    request = InferenceRequest(
        id="test_id", chat_request={"messages": [{"role": "user", "content": "Hello"}]}
    )

    async def mock_completion_generator():
        yield {"choices": [{"delta": {"content": "Response"}}]}

    mock_completion = AsyncMock()
    mock_completion.__aiter__.return_value = mock_completion_generator()

    with patch("openai.AsyncOpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = mock_completion

        llm = Llm()
        [item async for item in llm.execute(request, INFERENCE_BASE_URL)]

        MockOpenAI.assert_called_once_with(
            base_url=urljoin(INFERENCE_BASE_URL, "/v1"), api_key="sk-no-key-required"
        )
