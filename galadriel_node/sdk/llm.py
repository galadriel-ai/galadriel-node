from typing import AsyncGenerator
from urllib.parse import urljoin

import openai

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
        async for chunk in self._run_streaming_inference(request):
            yield chunk

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


def _llm_message_prefix(exc: Exception) -> str:
    return f"LLM Engine error: {str(exc)}"
