from typing import List
from typing import Optional
from typing import AsyncGenerator
from urllib.parse import urljoin

import openai

from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion_chunk import ChoiceLogprobs
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCallFunction
from galadriel_node.sdk.entities import LLMEngine
from galadriel_node.sdk.logging_utils import get_node_logger
from galadriel_node.sdk.protocol.entities import InferenceError
from galadriel_node.sdk.protocol.entities import InferenceRequest
from galadriel_node.sdk.protocol.entities import InferenceResponse
from galadriel_node.sdk.protocol.entities import InferenceStatusCodes
from galadriel_node.sdk.protocol.entities import InferenceErrorStatusCodes

logger = get_node_logger()


class Llm:
    def __init__(self, inference_base_url: str):
        base_url: str = urljoin(inference_base_url, "/v1")
        self._client = openai.AsyncOpenAI(
            base_url=base_url, api_key="sk-no-key-required"
        )
        self.engine = LLMEngine.VLLM

    async def detect_llm_engine(self) -> None:
        try:
            models = await self._client.models.list()
            match models.data[0].owned_by.lower():
                case "vllm":
                    self.engine = LLMEngine.VLLM
                case "lmdeploy":
                    self.engine = LLMEngine.LMDEPLOY
                case _:
                    # Default to VLLM
                    self.engine = LLMEngine.VLLM
        except Exception:
            pass

    async def execute(
        self,
        request: InferenceRequest,
        is_benchmark: bool = False,
    ) -> AsyncGenerator[InferenceResponse, None]:
        if not is_benchmark:
            logger.info(f"Running inference, id={request.id}")
        # Use streaming unless using LMDeploy with tools
        inference_function = (
            self._run_inference
            if self.engine == LLMEngine.LMDEPLOY and request.chat_request.get("tools")
            else self._run_streaming_inference
        )
        async for chunk in inference_function(request):
            yield chunk

    async def _run_inference(
        self, request: InferenceRequest
    ) -> AsyncGenerator[InferenceResponse, None]:
        try:
            # Disable streaming
            request.chat_request["stream"] = False
            completion = await self._client.chat.completions.create(
                **request.chat_request
            )
            chunk = self._convert_completion_to_chunk(completion)
            yield InferenceResponse(
                request_id=request.id,
                chunk=chunk,
                error=None,
                status=InferenceStatusCodes.RUNNING,
            )
            yield InferenceResponse(
                request_id=request.id,
                status=InferenceStatusCodes.DONE,
                chunk=None,
                error=None,
            )
        except Exception as exc:
            yield await self._handle_error(request.id, exc)

    async def _run_streaming_inference(
        self, request: InferenceRequest
    ) -> AsyncGenerator[InferenceResponse, None]:
        request.chat_request["stream"] = True
        request.chat_request["stream_options"] = {"include_usage": True}
        try:
            completion = await self._client.chat.completions.create(
                **request.chat_request
            )
            async for chunk in completion:
                yield InferenceResponse(
                    request_id=request.id,
                    status=InferenceStatusCodes.RUNNING,
                    chunk=chunk,
                )
            yield InferenceResponse(
                request_id=request.id,
                status=InferenceStatusCodes.DONE,
                chunk=None,
                error=None,
            )
        except Exception as exc:
            yield await self._handle_error(request.id, exc)

    async def _handle_error(self, request_id: str, exc: Exception) -> InferenceResponse:
        if isinstance(exc, openai.APIStatusError):
            status_code = InferenceErrorStatusCodes(exc.status_code)
        else:
            status_code = InferenceErrorStatusCodes.UNKNOWN_ERROR
        return InferenceResponse(
            request_id=request_id,
            status=InferenceStatusCodes.ERROR,
            error=InferenceError(
                status_code=status_code,
                message=_llm_message_prefix(exc),
            ),
        )

    def _convert_completion_to_chunk(
        self, completion: ChatCompletion
    ) -> ChatCompletionChunk:
        return ChatCompletionChunk(
            id=completion.id,
            created=completion.created,
            model=completion.model,
            object="chat.completion.chunk",
            service_tier=completion.service_tier,
            system_fingerprint=completion.system_fingerprint,
            usage=completion.usage,
            choices=self._convert_choices(completion.choices),
        )

    def _convert_choices(self, choices: list[Choice]) -> list[ChunkChoice]:
        chunk_choices = []
        for choice in choices:
            tool_calls: Optional[List[ChoiceDeltaToolCall]] = None
            if choice.message.tool_calls:
                tool_calls = [
                    ChoiceDeltaToolCall(
                        function=ChoiceDeltaToolCallFunction(
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        ),
                        id=tool_call.id,
                        index=index,
                        type=tool_call.type,
                    )
                    for index, tool_call in enumerate(choice.message.tool_calls)
                ]
            chunk_choices.append(
                ChunkChoice(
                    finish_reason=choice.finish_reason,
                    index=choice.index,
                    logprobs=(
                        ChoiceLogprobs(
                            content=choice.logprobs.content,
                            refusal=choice.logprobs.refusal,
                        )
                        if choice.logprobs
                        else None
                    ),
                    delta=ChoiceDelta(
                        content=choice.message.content,
                        refusal=choice.message.refusal,
                        role=choice.message.role,
                        tool_calls=tool_calls,
                    ),
                )
            )
        return chunk_choices


def _llm_message_prefix(exc: Exception) -> str:
    return f"LLM Engine error: {str(exc)}"
