from urllib.parse import urljoin

import openai
import pytest
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionChunk
from openai.types.chat import ChatCompletionMessage
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.completion_usage import CompletionUsage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCallFunction
from openai.types.chat.chat_completion_message_tool_call import Function
from unittest.mock import AsyncMock, MagicMock, patch
from galadriel_node.sdk.entities import (
    LLMEngine,
    InferenceError,
    InferenceRequest,
    InferenceResponse,
    InferenceStatusCodes,
)
from galadriel_node.sdk.llm import Llm

INFERENCE_BASE_URL = "https://api.openai.com/v1"


def _get_mock_completion() -> ChatCompletion:
    return ChatCompletion(
        id="test_id",
        created=1234567890,
        model="test_model",
        object="chat.completion",
        service_tier=None,
        system_fingerprint="fingerprint",
        usage=CompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(
                    content="hello",
                    role="assistant",
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            id="test_id",
                            function=Function(arguments="{}", name="test_function"),
                            type="function",
                        )
                    ],
                ),
            )
        ],
    )


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
        llm = Llm(INFERENCE_BASE_URL)
        # Spy on `_run_streaming_inference` to check if it was called
        with patch.object(
            llm, "_run_streaming_inference", wraps=llm._run_streaming_inference
        ) as mock_run_streaming_inference:
            results = [item async for item in llm.execute(request)]

            assert len(results) == 2
            assert isinstance(results[0], InferenceResponse)
            assert results[0].chunk == {"choices": [{"delta": {"content": "chunk1"}}]}
            assert results[0].error is None
            assert isinstance(results[1], InferenceResponse)
            assert results[1].chunk == {"choices": [{"delta": {"content": "chunk2"}}]}
            assert results[1].error is None
            mock_run_streaming_inference.assert_called_once_with(request)


async def test_llm_execute_lmdeploy_tools():
    request = InferenceRequest(
        id="test_id",
        chat_request={"stream": True, "tools": ["fake_tool"]},
    )

    mock_openai = AsyncMock()
    mock_openai.chat.completions.create.return_value = _get_mock_completion()

    with patch("openai.AsyncOpenAI", return_value=mock_openai):
        llm = Llm(INFERENCE_BASE_URL)
        llm.engine = LLMEngine.LMDEPLOY
        # Spy on `_run_inference` to check if it was called
        with patch.object(
            llm, "_run_inference", wraps=llm._run_inference
        ) as mock_run_inference:
            results = [item async for item in llm.execute(request)]

            assert len(results) == 2
            assert isinstance(results[0], InferenceResponse)
            assert results[0].chunk.choices[0].delta.content == "hello"
            assert results[0].error is None
            assert isinstance(results[1], InferenceResponse)
            assert results[1].chunk.choices == []
            assert results[1].error is None
            mock_run_inference.assert_called_once_with(request)


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

        llm = Llm(INFERENCE_BASE_URL)
        results = [item async for item in llm.execute(request)]

        assert len(results) == 1
        assert isinstance(results[0], InferenceResponse)
        assert results[0].error is not None
        assert results[0].error.status_code == InferenceStatusCodes.BAD_REQUEST
        assert results[0].error.message == "LLM Engine error: Inference failed"


async def test_llm_execute_with_generic_exception():
    request = InferenceRequest(id="test_id", chat_request={"stream": True})

    with patch("openai.AsyncOpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception(
            "Inference failed"
        )

        llm = Llm(INFERENCE_BASE_URL)
        results = [item async for item in llm.execute(request)]

        assert len(results) == 1
        assert isinstance(results[0], InferenceResponse)
        assert results[0].error is not None
        assert results[0].error.status_code == InferenceStatusCodes.UNKNOWN_ERROR
        assert results[0].error.message == "LLM Engine error: Inference failed"


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

        llm = Llm(INFERENCE_BASE_URL)
        [item async for item in llm.execute(request)]

        MockOpenAI.assert_called_once_with(
            base_url=urljoin(INFERENCE_BASE_URL, "/v1"), api_key="sk-no-key-required"
        )


async def test_llm_handle_error_with_status_code():
    llm = Llm(INFERENCE_BASE_URL)
    error = openai.APIStatusError(
        "API Error", response=MagicMock(status_code=403), body=None
    )

    response = await llm._handle_error("test_id", error)

    assert isinstance(response, InferenceResponse)
    assert response.request_id == "test_id"
    assert isinstance(response.error, InferenceError)
    assert response.error.status_code == InferenceStatusCodes.PERMISSION_DENIED
    assert response.error.message == "LLM Engine error: API Error"


async def test_llm_handle_unknown_error():
    llm = Llm(INFERENCE_BASE_URL)
    error = Exception("Unexpected error")

    response = await llm._handle_error("test_id", error)

    assert isinstance(response, InferenceResponse)
    assert response.request_id == "test_id"
    assert isinstance(response.error, InferenceError)
    assert response.error.status_code == InferenceStatusCodes.UNKNOWN_ERROR
    assert response.error.message == "LLM Engine error: Unexpected error"


@pytest.mark.parametrize(
    "owned_by, llm_engine",
    [
        ("vllm", LLMEngine.VLLM),  # Detects vLLM properly
        ("lmdeploy", LLMEngine.LMDEPLOY),  # Detects LMDeploy properly
        ("some_llm_engine", LLMEngine.VLLM),  # Unknown engine - act as if it's vLLM
    ],
)
async def test_detect_llm_engine(owned_by: str, llm_engine: LLMEngine):
    llm = Llm(INFERENCE_BASE_URL)
    llm._client = AsyncMock()
    mock_model_response = MagicMock()
    mock_model_response.data = [MagicMock(owned_by=owned_by)]
    llm._client.models.list.return_value = mock_model_response

    result = await llm.detect_llm_engine()
    assert result == llm_engine
    assert llm.engine == llm_engine


@pytest.mark.asyncio
async def test_convert_completion_to_chunks():
    # Initialize Llm instance
    llm = Llm("https://api.openai.com/v1")

    mock_completion = _get_mock_completion()
    chunks = await llm._convert_completion_to_chunks(mock_completion)

    assert len(chunks) == 2
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)

    assert chunks[0].id == "test_id"
    assert chunks[0].created == 1234567890
    assert chunks[0].model == "test_model"
    assert chunks[0].object == "chat.completion.chunk"
    assert chunks[0].service_tier == None
    assert chunks[0].system_fingerprint == "fingerprint"
    assert chunks[0].usage == CompletionUsage(
        completion_tokens=20, prompt_tokens=10, total_tokens=30
    )
    assert chunks[0].choices == [
        ChunkChoice(
            delta=ChoiceDelta(
                content="hello",
                role="assistant",
                tool_calls=[
                    ChoiceDeltaToolCall(
                        id="test_id",
                        index=0,
                        function=ChoiceDeltaToolCallFunction(
                            arguments="{}", name="test_function"
                        ),
                        type="function",
                    )
                ],
            ),
            index=0,
            finish_reason="stop",
        )
    ]

    assert chunks[1].id == "test_id"
    assert chunks[1].created == 1234567890
    assert chunks[1].model == "test_model"
    assert chunks[1].object == "chat.completion.chunk"
    assert chunks[1].service_tier == None
    assert chunks[1].system_fingerprint == "fingerprint"
    assert chunks[1].usage == CompletionUsage(
        completion_tokens=20, prompt_tokens=10, total_tokens=30
    )
    assert chunks[1].choices == []
